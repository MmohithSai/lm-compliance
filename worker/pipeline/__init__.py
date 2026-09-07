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
from .models import PipelineResult, ScaleSource, ScanContext, ScanRow, Word
from .ocr import ocr_words
from .preprocess import preprocess
from .rules_engine import run_rules, score

log = logging.getLogger("worker")

# (preprocessed image, image_id, languages) -> line boxes. Only the eval passes anything but
# `ocr_words`: it wraps it in a disk cache so a rerun measures a changed extractor, not PaddleOCR
# reading the same 280 photos again.
OcrFn = Callable[[NDArray[np.uint8], str, list[str]], list[Word]]


def run_local(images: list[Path], ctx: ScanContext, ocr: OcrFn = ocr_words) -> PipelineResult:
    """preprocess -> ocr -> extract -> measure -> rules -> score. No network."""
    words: list[Word] = []
    for path in images:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"unreadable image: {path.name}")
        page = preprocess(cast("NDArray[np.uint8]", img))
        for word in ocr(page, path.stem, ctx.languages):
            words.append(word.model_copy(update={"id": len(words)}))

    declarations = RegexLayoutExtractor().extract(words, ctx)
    # measure is P4: without a scale mm_per_px stays None and the font checks say unverifiable.
    try:
        violations = run_rules(declarations, ctx)
    except NotImplementedError:
        log.warning("rule engine not built yet (P3), no violations and a score of 100")
        violations = []

    return PipelineResult(
        words=words,
        declarations=declarations,
        violations=violations,
        mm_per_px=None,
        scale_source=ScaleSource.none,
        compliance_score=score(violations),
    )


def context_for(scan: ScanRow) -> ScanContext:
    """What the inspector told us on the upload form. Everything else stays at its default."""
    area = None
    if scan.pdp_width_mm and scan.pdp_height_mm:
        area = scan.pdp_width_mm * scan.pdp_height_mm / 100  # mm² -> cm²
    return ScanContext(source=scan.source, pdp_area_cm2=area)


def run_scan(sb: Client, scan: ScanRow) -> PipelineResult:
    """Download the scan's images, run_local, write words/declarations/violations back."""
    images = cast(
        list[dict[str, Any]],
        sb.table("scan_images").select("id, storage_path").eq("scan_id", scan.id).execute().data,
    )
    if not images:
        raise ValueError("scan has no images")

    with TemporaryDirectory() as tmp:
        # Named by scan_images.id so Word.image_id maps straight back to a row.
        paths = []
        for img in images:
            path = Path(tmp) / f"{img['id']}.jpg"
            path.write_bytes(sb.storage.from_("scans").download(img["storage_path"]))
            paths.append(path)
        result = run_local(paths, context_for(scan))

    store(sb, scan.id, result)
    return result


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
