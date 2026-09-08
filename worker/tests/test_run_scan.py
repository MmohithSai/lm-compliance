"""run_scan against a fake Supabase client: images downloaded, rows written, word_ids remapped."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from supabase import Client

from pipeline import run_scan, store
from pipeline.models import (
    Declaration,
    Evidence,
    PipelineResult,
    ScaleSource,
    ScanContext,
    ScanRow,
    Severity,
    Violation,
    Word,
)
from pipeline.product import link_product


class FakeTable:
    def __init__(self, name: str, db: FakeClient) -> None:
        self.name, self.db, self.rows = name, db, cast(list[dict[str, Any]], [])

    def select(self, _cols: str) -> FakeTable:
        return self

    def eq(self, _col: str, _val: str) -> FakeTable:
        return self

    def insert(self, rows: list[dict[str, Any]]) -> FakeTable:
        self.rows = rows
        return self

    def upsert(self, row: dict[str, Any], on_conflict: str = "") -> FakeTable:
        self.db.upserted.setdefault(self.name, []).append((row, on_conflict))
        self.rows = [row]  # Postgres returns the row it wrote, id and all
        return self

    def update(self, row: dict[str, Any]) -> FakeTable:
        self.db.updated.setdefault(self.name, []).append(row)
        return self

    def execute(self) -> FakeTable:
        if self.rows:
            # Postgres assigns ocr_words ids; deliberately not 1..n, so a bad remap shows up.
            self.db.written[self.name] = [{**r, "id": 900 + i} for i, r in enumerate(self.rows)]
        return self

    @property
    def data(self) -> list[dict[str, Any]]:
        return self.db.written.get(self.name, self.db.seed.get(self.name, []))


class FakeBucket:
    def __init__(self, db: FakeClient) -> None:
        self.db = db

    def download(self, path: str) -> bytes:
        self.db.downloaded.append(path)
        return b"jpeg-bytes"

    def upload(self, path: str, data: bytes, options: dict[str, str]) -> None:
        self.db.uploaded[path] = (data, options)


class FakeStorage:
    def __init__(self, db: FakeClient) -> None:
        self.db = db

    def from_(self, _bucket: str) -> FakeBucket:
        return FakeBucket(self.db)


class FakeClient:
    def __init__(self, seed: dict[str, list[dict[str, Any]]]) -> None:
        self.seed = seed
        self.written: dict[str, list[dict[str, Any]]] = {}
        self.upserted: dict[str, list[tuple[dict[str, Any], str]]] = {}
        self.updated: dict[str, list[dict[str, Any]]] = {}
        self.downloaded: list[str] = []
        self.uploaded: dict[str, tuple[bytes, dict[str, str]]] = {}
        self.storage = FakeStorage(self)

    def table(self, name: str) -> FakeTable:
        return FakeTable(name, self)


SCAN = ScanRow(
    id="s1",
    inspector_id="u1",
    pdp_width_mm=60,
    pdp_height_mm=40,
    created_at=datetime(2026, 9, 8, 10, 30, tzinfo=UTC),
)
IMAGES = [
    {"id": "img-a", "storage_path": "s1/0.jpg", "kind": "front"},
    {"id": "img-b", "storage_path": "s1/1.jpg", "kind": "back"},
]


WORDS = [Word(id=i, image_id="img-a", text="x", x=0, y=0, w=1, h=1, confidence=0.9) for i in (1, 2)]
RESULT = PipelineResult(
    words=WORDS,
    declarations=[Declaration(field="mrp", value="MRP 20", word_ids=[2])],
    violations=[
        Violation(
            rule_id="D1",
            rule_ref="6(1)(a)",
            severity=Severity.critical,
            message="missing",
            evidence=Evidence(word_ids=[1, 2]),
        )
    ],
    mm_per_px=None,
    scale_source=ScaleSource.none,
    compliance_score=75,
)


def fake(**seed: list[dict[str, Any]]) -> FakeClient:
    return FakeClient({"scan_images": IMAGES, **seed})


def test_run_scan_downloads_every_image_and_stores_what_the_pipeline_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pipeline itself is covered by the eval harness; this pins the wiring around it."""
    seen: list[list[str]] = []

    def fake_pipeline(images: list[Path], ctx: ScanContext) -> PipelineResult:
        seen.append([p.stem for p in images])  # named by scan_images.id, for Word.image_id
        assert ctx.pdp_area_cm2 == 24.0  # 60 x 40 mm
        return RESULT

    db = fake()
    monkeypatch.setattr("pipeline.run_local", fake_pipeline)
    result = run_scan(cast(Client, db), SCAN)
    assert db.downloaded == ["s1/0.jpg", "s1/1.jpg"]
    assert seen == [["img-a", "img-b"]]
    assert result.compliance_score == 75
    assert db.written["declarations"][0]["value"] == "MRP 20"


def test_run_scan_without_images_fails_loudly() -> None:
    db = FakeClient({"scan_images": []})
    with pytest.raises(ValueError, match="no images"):
        run_scan(cast(Client, db), SCAN)


def test_store_remaps_word_ids_to_the_ids_postgres_assigned() -> None:
    db = fake()
    store(cast(Client, db), "s1", RESULT)
    assert [w["id"] for w in db.written["ocr_words"]] == [900, 901]
    assert db.written["ocr_words"][0]["scan_id"] == "s1"
    assert db.written["declarations"][0]["word_ids"] == [901]
    assert db.written["violations"][0]["evidence"]["word_ids"] == [900, 901]


def test_store_writes_nothing_when_the_result_is_empty() -> None:
    db = fake()
    store(
        cast(Client, db),
        "s1",
        PipelineResult(
            words=[],
            declarations=[],
            violations=[],
            mm_per_px=None,
            scale_source=ScaleSource.none,
            compliance_score=100,
        ),
    )
    assert db.written == {}


def test_run_scan_fails_when_the_ocr_read_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """score([]) is 100 by construction, so an unreadable photo would otherwise finish `done`
    with a perfect score. Scan 5e0811b8 did exactly that and showed "100 / 100" for a pack the
    pipeline never read."""
    empty = RESULT.model_copy(update={"words": [], "declarations": [], "violations": []})
    db = fake()
    monkeypatch.setattr("pipeline.run_local", lambda images, ctx: empty)
    with pytest.raises(ValueError, match="no text was read"):
        run_scan(cast(Client, db), SCAN)
    assert db.written == {}


# ---------------------------------------------------------------- P6: filing a scan under a pack

PACK = [
    Declaration(field="manufacturer", value="Mfd by: Parle Products Pvt Ltd, Mumbai 400057"),
    Declaration(field="generic_name", value="Common Name: Biscuits"),
]


def test_a_scan_is_filed_under_the_product_its_declarations_name() -> None:
    db = fake()
    product_id = link_product(cast(Client, db), "s1", PACK)
    row, on_conflict = db.upserted["products"][0]
    assert on_conflict == "match_key"  # the second photo of this pack must land on this row
    assert row == {
        "match_key": "parle products|biscuits",
        "name": "Biscuits",
        "manufacturer": "Parle Products Pvt Ltd, Mumbai 400057",
    }
    assert db.updated["scans"] == [{"product_id": product_id}]


def test_a_pack_with_no_generic_name_is_named_after_its_maker() -> None:
    db = fake()
    link_product(cast(Client, db), "s1", PACK[:1])
    row, _ = db.upserted["products"][0]
    assert row["match_key"] == "parle products|"
    assert row["name"] == "Parle Products Pvt Ltd"


def test_the_maker_s_street_does_not_end_up_in_the_product_s_name() -> None:
    """The Reynolds pen on the hosted project: PP-OCR dropped the comma after "Limited", and
    the repository listed the product as "…Private Limited Plot No. C-21"."""
    db = fake()
    link_product(
        cast(Client, db),
        "s1",
        [
            Declaration(
                field="manufacturer",
                value="Manufactured,Marketed and Brand Owned bye Reynolds Pens India Private "
                "Limited Plot No. C-21, SlPCOT Industrial Park",
            )
        ],
    )
    assert db.upserted["products"][0][0]["name"] == "Reynolds Pens India Private Limited"


def test_an_imported_pack_is_filed_under_its_importer() -> None:
    db = fake()
    link_product(
        cast(Client, db),
        "s1",
        [Declaration(field="importer", value="Imported by: Nestle India Ltd, Gurugram")],
    )
    assert db.upserted["products"][0][0]["match_key"] == "nestle india|"


def test_a_pack_that_names_no_maker_is_filed_under_nothing() -> None:
    """Which is D1, and a product row invented here would put another pack's scans in its
    history. The scan stays searchable by its inspector, place and note."""
    db = fake()
    assert link_product(cast(Client, db), "s1", [Declaration(field="mrp", value="MRP 20")]) is None
    assert db.upserted == {} and db.updated == {}


def test_run_scan_files_the_scan_it_just_stored(monkeypatch: pytest.MonkeyPatch) -> None:
    db = fake()
    monkeypatch.setattr(
        "pipeline.run_local", lambda images, ctx: RESULT.model_copy(update={"declarations": PACK})
    )
    run_scan(cast(Client, db), SCAN)
    assert db.upserted["products"][0][0]["match_key"] == "parle products|biscuits"
    assert db.updated["scans"] == [{"product_id": "900"}]
