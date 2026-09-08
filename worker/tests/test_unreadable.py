"""P8. A photograph or screenshot nobody can read gets a sentence, never a verdict.

`score([])` is 100 by construction, so the dangerous failure here is silence: a blurred pack
that reaches `done` with 100 / 100, or a cropped listing whose empty extraction is reported as
"missing everything" under Rule 6(10). Both are refused before anything is written.

The threshold itself is `MIN_READABLE_CHARS` and the evidence for it is in the comment beside
it; these tests pin the behaviour it produces, not the number.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from supabase import Client

from main import process_one
from pipeline import MIN_READABLE_CHARS, UnreadableScan, run_scan, unreadable
from pipeline.models import (
    Declaration,
    PipelineResult,
    ScaleSource,
    ScanRow,
    Source,
    Word,
)
from tests.test_run_scan import IMAGES, RESULT, FakeClient


def result(*texts: str) -> PipelineResult:
    """A finished pipeline run that read exactly these lines and found nothing else."""
    return PipelineResult(
        words=[
            Word(id=i, image_id="img-a", text=t, x=0, y=40 * i, w=10 * len(t), h=30, confidence=c)
            for i, (t, c) in enumerate((t, 0.95) for t in texts)
        ],
        declarations=[],
        violations=[],
        mm_per_px=None,
        scale_source=ScaleSource.none,
        compliance_score=100,
    )


# A real pack reads 134 to 1,906 characters and a listing 5,300 to 10,100; the blurred, shrunk
# and motion-blurred variants of one real Amazon tile read 44 to 59. These stand in for both.
LEGIBLE = result(
    "Mfd by: Brite Foods Pvt Ltd, Plot 12, MIDC, Pune 411019",
    "Net Qty: 200 g",
    "MRP Rs 20.00 (Inclusive of all taxes)",
)
BLURRED = result("tata", "salt", "1kg  32")


# ---------------------------------------------------------------- what counts as unreadable


def test_a_pack_with_its_declarations_on_it_is_readable() -> None:
    assert unreadable(LEGIBLE, Source.package) is None
    assert unreadable(LEGIBLE, Source.ecommerce) is None


def test_a_sparse_but_legible_pack_is_not_refused() -> None:
    """The floor has to sit under the least legible thing in eval/dataset, or it costs the
    inspector real scans. A one-line sachet reads about 134 characters."""
    assert len("".join(w.text for w in LEGIBLE.words)) < 2 * MIN_READABLE_CHARS
    assert unreadable(LEGIBLE, Source.package) is None


def test_no_ocr_words_at_all_cannot_be_assessed() -> None:
    why = unreadable(result(), Source.package)
    assert why is not None
    assert why.startswith("No text at all could be read")


def test_a_handful_of_headline_words_cannot_be_assessed() -> None:
    """PP-OCR answers a blurred panel by not detecting the small print and still reports the
    few large words at 0.95, so the count is what falls, not the confidence."""
    why = unreadable(BLURRED, Source.ecommerce)
    assert why is not None
    assert why.startswith("Only 15 characters of text could be read")


# ---------------------------------------------------------------- what the inspector is told


def test_the_message_for_a_package_says_what_to_re_shoot() -> None:
    why = unreadable(result(), Source.package)
    assert why is not None
    assert "these photographs" in why
    assert "blurry" in why and "cropped" in why and "glare" in why
    assert "Photograph the declaration panel again" in why


def test_the_message_for_a_listing_says_what_to_upload_instead() -> None:
    why = unreadable(result(), Source.ecommerce)
    assert why is not None
    assert "this screenshot" in why
    assert "blurry" in why and "cropped" in why and "low-resolution" in why
    assert "Upload a clearer, full-size screenshot" in why


@pytest.mark.parametrize("source", list(Source))
def test_the_message_never_reads_as_a_verdict(source: Source) -> None:
    """Not "compliant", not "non-compliant", and not a score. Nothing was checked."""
    why = unreadable(result(), source)
    assert why is not None
    assert "not checked against the Rules" in why
    assert "compliant" not in why.casefold()
    assert "100" not in why


@pytest.mark.parametrize("source", list(Source))
def test_the_message_fits_the_error_column(source: Source) -> None:
    """`scans.error` is truncated to 500 characters by the loop; a message cut mid-sentence
    would lose the half that says what to do."""
    why = unreadable(result(), source)
    assert why is not None and len(why) <= 500


# ---------------------------------------------------------------- nothing is written for it


def unreadable_scan(monkeypatch: pytest.MonkeyPatch, empty: PipelineResult) -> FakeClient:
    db = FakeClient({"scan_images": IMAGES})
    monkeypatch.setattr("pipeline.run_local", lambda images, ctx: empty)
    return db


PACK = ScanRow(id="s1", inspector_id="u1")
LISTING = ScanRow(id="s1", inspector_id="u1", source=Source.ecommerce)


def test_an_unreadable_pack_stops_the_scan_before_a_single_row_is_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = unreadable_scan(monkeypatch, result())
    with pytest.raises(UnreadableScan, match="Photograph the declaration panel again"):
        run_scan(cast(Client, db), PACK)
    assert db.written == {}  # no words, no declarations, no violations
    assert db.upserted == {}  # no reports row, no product
    assert db.uploaded == {}  # no report.pdf / .docx / .json in Storage


def test_an_unreadable_listing_is_told_about_the_screenshot_and_not_the_pack(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = unreadable_scan(monkeypatch, BLURRED)
    with pytest.raises(UnreadableScan, match="Upload a clearer, full-size screenshot"):
        run_scan(cast(Client, db), LISTING)
    assert db.uploaded == {}


def test_a_readable_scan_still_goes_all_the_way_through(monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard must not stand between a normal scan and its report."""
    db = FakeClient({"scan_images": IMAGES})
    readable = RESULT.model_copy(
        update={
            "words": LEGIBLE.words,
            "declarations": [Declaration(field="mrp", value="MRP 20", word_ids=[2])],
        }
    )
    monkeypatch.setattr("pipeline.run_local", lambda images, ctx: readable)
    run_scan(cast(Client, db), PACK)
    assert db.written["ocr_words"]
    assert "s1/report.json" in db.uploaded


# ---------------------------------------------------------------- what reaches scans.error


class LoopClient(FakeClient):
    """FakeClient plus the one RPC the worker loop calls to claim a scan."""

    def __init__(self, scan: ScanRow) -> None:
        super().__init__({"scan_images": IMAGES})
        self.scan = scan

    def rpc(self, _name: str, _args: dict[str, Any] | None = None) -> LoopClient:
        return self

    def execute(self) -> LoopClient:
        return self

    @property
    def data(self) -> list[dict[str, Any]]:
        return [self.scan.model_dump(mode="json")]


def stored_error(db: LoopClient) -> str:
    (update,) = db.updated["scans"]
    return cast(str, update["error"])


def test_the_inspector_reads_the_sentence_and_not_the_exception_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`ValueError: no text was read...` is what the log wants and not what a scan page should
    put in front of an inspector."""
    db = LoopClient(LISTING)
    monkeypatch.setattr("pipeline.run_local", lambda images, ctx: result())
    assert process_one(cast(Client, db)) is True
    error = stored_error(db)
    assert error.startswith("No text at all could be read from this screenshot")
    assert "Error" not in error and ":" not in error.split(".")[0]
    assert db.updated["scans"][0]["status"] == "failed"
    assert "compliance_score" not in db.updated["scans"][0]


def test_a_real_crash_keeps_its_class_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the unreadable case is rewritten. A bug still reaches the log and the row as one."""
    db = LoopClient(PACK)

    def boom(images: Any, ctx: Any) -> PipelineResult:
        raise KeyError("declarations")

    monkeypatch.setattr("pipeline.run_local", boom)
    process_one(cast(Client, db))
    assert stored_error(db).startswith("KeyError:")
