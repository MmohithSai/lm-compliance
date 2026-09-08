"""Pipeline entry points. `run_local` is what the eval harness calls; `run_scan` wraps it."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

import cv2
import numpy as np
from numpy.typing import NDArray
from supabase import Client

from .extractors.regex_layout import RegexLayoutExtractor
from .measure import measure_declarations, pdp_area_cm2, resolve_scale
from .models import (
    PipelineResult,
    ReportImage,
    ScaleSource,
    ScanContext,
    ScanRow,
    Source,
    Word,
)
from .ocr import ocr_words
from .preprocess import preprocess
from .product import link_product
from .report import annotate_panels, build_report, render_docx, render_html, render_json, render_pdf
from .rules_engine import run_rules, score

log = logging.getLogger("worker")


class UnreadableScan(ValueError):
    """The photographs hold too little text to judge. Its message is written for the inspector
    and the loop stores it on the scan word for word, without the exception's class name."""


# ---------------------------------------------------------------- is there anything to judge?
# A scan is judged on the text PP-OCR returned, and below this much text there is nothing to
# judge. Measured over the 57 eval cases in `eval/.ocr_cache`: the least legible of them returns
# 134 characters (a one line sachet), the least legible photograph 139, and a listing screenshot
# 5,300 to 10,100. Blurring, shrinking and motion blurring one real Amazon tile until it is
# unreadable takes it from 218 characters to 44-59.
#
# The count is the signal and the confidence is not: PP-OCR answers a blurred panel by not
# *detecting* the small print, and reports the few headline words it still finds at 0.94-0.97 —
# through a 31 px Gaussian blur, a 8x downscale and an 82% darkening alike. Only motion blur
# drags confidence down, and that case is already well under the floor on count. A second
# threshold on a number that does not move would refuse legible packs and catch nothing.
# Raise this if a legible pack is ever refused; the evidence for it is in docs/ARCHITECTURE.md.
MIN_READABLE_CHARS = 80

# What the inspector reads on the scan, and the only text stored in `scans.error` for this case.
CANNOT_ASSESS = {
    Source.package: (
        "{read} could be read from these photographs, so this pack was not checked against the "
        "Rules. The photographs may be blurry, shot from too far away, cropped, or lost to "
        "glare. Photograph the declaration panel again, filling the frame with it and holding "
        "the phone steady."
    ),
    Source.ecommerce: (
        "{read} could be read from this screenshot, so this listing was not checked against the "
        "Rules. The screenshot may be blurry, cropped, or too low-resolution. Upload a clearer, "
        "full-size screenshot of the listing that includes the product details table."
    ),
}


def unreadable(result: PipelineResult, source: Source) -> str | None:
    """Why this scan cannot be assessed, in the inspector's words, or None if it can be."""
    chars = sum(len(w.text) for w in result.words)
    if chars >= MIN_READABLE_CHARS:
        return None
    read = "No text at all" if not chars else f"Only {chars} characters of text"
    return CANNOT_ASSESS[source].format(read=read)


# (preprocessed image, image_id, languages) -> line boxes. Only the eval passes anything but
# `ocr_words`: it wraps it in a disk cache so a rerun measures a changed extractor, not PaddleOCR
# reading the same 280 photos again.
OcrFn = Callable[[NDArray[np.uint8], str, list[str]], list[Word]]


def run_local(images: list[Path], ctx: ScanContext, ocr: OcrFn = ocr_words) -> PipelineResult:
    """preprocess -> ocr -> extract -> measure -> rules -> score. No network."""
    words: list[Word] = []
    # The photographs as uploaded, and one scale each. Measurements are taken off these and not
    # off the preprocessed copies: preprocess equalises contrast, and measuring contrast after
    # that would measure the equalisation. It moves no pixel, so the OCR boxes fit both.
    pages: dict[str, NDArray[np.uint8]] = {}
    scales: dict[str, tuple[float | None, ScaleSource]] = {}
    for path in images:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"unreadable image: {path.name}")
        raw = cast("NDArray[np.uint8]", img)
        page = preprocess(raw)
        for word in ocr(page, path.stem, ctx.languages):
            words.append(word.model_copy(update={"id": len(words)}))
        pages[path.stem] = raw
        # Per photograph, never borrowed: a marker in one frame says nothing about the distance
        # the next frame was shot from. The inspector's panel width is read against this photo's
        # own width, which assumes the panel fills the frame — what the upload form asks for.
        scales[path.stem] = resolve_scale(
            raw, ctx.pdp_width_mm, raw.shape[1], ctx.has_reference_card
        )

    declarations = measure_declarations(
        RegexLayoutExtractor().extract(words, ctx),
        words,
        pages,
        {image_id: scale for image_id, (scale, _source) in scales.items()},
    )
    # The scan carries one scale, and it is the first frame that had a reference in it. The font
    # checks read each declaration's own height_mm; this only says whether anything was measured.
    mm_per_px, scale_source = next(
        ((s, src) for s, src in scales.values() if s is not None), (None, ScaleSource.none)
    )
    violations = run_rules(
        declarations, ctx.model_copy(update={"mm_per_px": mm_per_px, "scale_source": scale_source})
    )

    return PipelineResult(
        words=words,
        declarations=declarations,
        violations=violations,
        mm_per_px=mm_per_px,
        scale_source=scale_source,
        compliance_score=score(violations),
    )


def context_for(scan: ScanRow) -> ScanContext:
    """What the inspector told us on the upload form. Everything else stays at its default."""
    area = None
    if scan.pdp_width_mm and scan.pdp_height_mm:
        area = pdp_area_cm2(scan.pdp_width_mm, scan.pdp_height_mm)
    return ScanContext(
        source=scan.source,
        pdp_area_cm2=area,
        pdp_width_mm=scan.pdp_width_mm,
        has_reference_card=scan.has_reference_card,
    )


def run_scan(sb: Client, scan: ScanRow) -> PipelineResult:
    """Download the scan's images, run_local, write words/declarations/violations back."""
    images = cast(
        list[dict[str, Any]],
        sb.table("scan_images")
        .select("id, storage_path, kind")
        .eq("scan_id", scan.id)
        .execute()
        .data,
    )
    if not images:
        raise ValueError("scan has no images")

    ctx = context_for(scan)
    with TemporaryDirectory() as tmp:
        # Named by scan_images.id so Word.image_id maps straight back to a row.
        paths = {}
        for img in images:
            path = Path(tmp) / f"{img['id']}.jpg"
            path.write_bytes(sb.storage.from_("scans").download(img["storage_path"]))
            paths[str(img["id"])] = path
        result = run_local(list(paths.values()), ctx)

        # A scan the OCR could not read is a failed read, not a compliant pack. score([]) is
        # 100 by construction, and letting that reach `done` puts "100 / 100" on the report for
        # a photograph nobody could read — the one wrong answer this project must never give.
        # Raised before `store`, so no declarations, no violations and no report file exist for
        # a scan that was never assessed. The loop turns it into `failed` plus this sentence.
        if (why := unreadable(result, ctx.source)) is not None:
            raise UnreadableScan(why)

        store(sb, scan.id, result)
        # Inside the temp directory: the report embeds the photographs it cites, and once this
        # block exits they are gone.
        publish_report(
            sb,
            scan,
            result,
            ctx,
            [
                ReportImage(id=str(i["id"]), kind=str(i["kind"]), storage_path=i["storage_path"])
                for i in images
            ],
            paths,
        )
    # After the rows are written, and outside the temp directory: filing the scan under a
    # product needs the declarations, not the photographs.
    link_product(sb, scan.id, result.declarations)
    return result


REPORT_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "json": "application/json",
}


def publish_report(
    sb: Client,
    scan: ScanRow,
    result: PipelineResult,
    ctx: ScanContext,
    images: list[ReportImage],
    paths: dict[str, Path],
) -> dict[str, str | None]:
    """Render the three report files and upload them to `scans/<scan id>/report.*`.

    A format that fails to render is logged and stored as a null path rather than failing the
    scan: the analysis is the result, the files are a rendering of it, and WeasyPrint needs
    system libraries (Pango, Cairo) that a machine can be missing. The detail page reads the
    paths and offers only what exists.
    """
    report = build_report(scan, result, ctx, images)
    panels = annotate_panels(paths, report)
    render: dict[str, Callable[[], bytes]] = {
        "json": lambda: render_json(report).encode("utf-8"),
        "pdf": lambda: render_pdf(render_html(report, panels)),
        "docx": lambda: render_docx(report, panels),
    }

    stored: dict[str, str | None] = {}
    for ext, make in render.items():
        path = f"{scan.id}/report.{ext}"
        try:
            data = make()
            sb.storage.from_("scans").upload(
                path, data, {"content-type": REPORT_MIME[ext], "upsert": "true"}
            )
        except Exception:  # noqa: BLE001 - one missing format must not lose the other two
            log.exception("could not write report.%s for scan %s", ext, scan.id)
            stored[ext] = None
        else:
            stored[ext] = path

    sb.table("reports").upsert(
        {
            "scan_id": scan.id,
            "pdf_path": stored["pdf"],
            "docx_path": stored["docx"],
            "json_path": stored["json"],
        },
        on_conflict="scan_id",
    ).execute()
    return stored


def store(sb: Client, scan_id: str, result: PipelineResult) -> None:
    """Write the result rows. ocr_words ids are assigned by Postgres, so word_ids are remapped."""
    word_id = {}
    if result.words:
        rows = cast(
            list[dict[str, Any]],
            sb.table("ocr_words")
            .insert([{"scan_id": scan_id, **w.model_dump(exclude={"id"})} for w in result.words])
            .execute()
            .data,
        )
        word_id = {w.id: row["id"] for w, row in zip(result.words, rows, strict=True)}

    if result.declarations:
        sb.table("declarations").insert(
            [
                {
                    "scan_id": scan_id,
                    **d.model_dump(exclude={"word_ids", "contrast"}),
                    "word_ids": [word_id[i] for i in d.word_ids],
                }
                for d in result.declarations
            ]
        ).execute()

    if result.violations:
        sb.table("violations").insert(
            [
                {
                    "scan_id": scan_id,
                    **v.model_dump(exclude={"evidence"}),
                    "evidence": {
                        **v.evidence.model_dump(exclude={"word_ids"}),
                        "word_ids": [word_id[i] for i in v.evidence.word_ids],
                    },
                }
                for v in result.violations
            ]
        ).execute()
