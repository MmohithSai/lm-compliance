"""run_scan against a fake Supabase client: images downloaded, rows written, word_ids remapped."""

from __future__ import annotations

from typing import Any, cast

import pytest
from supabase import Client

from pipeline import run_scan, store
from pipeline.models import (
    Declaration,
    Evidence,
    PipelineResult,
    ScaleSource,
    ScanRow,
    Severity,
    Violation,
    Word,
)


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


class FakeStorage:
    def __init__(self, db: FakeClient) -> None:
        self.db = db

    def from_(self, _bucket: str) -> FakeBucket:
        return FakeBucket(self.db)


class FakeClient:
    def __init__(self, seed: dict[str, list[dict[str, Any]]]) -> None:
        self.seed = seed
        self.written: dict[str, list[dict[str, Any]]] = {}
        self.downloaded: list[str] = []
        self.storage = FakeStorage(self)

    def table(self, name: str) -> FakeTable:
        return FakeTable(name, self)


SCAN = ScanRow(id="s1", inspector_id="u1", pdp_width_mm=60, pdp_height_mm=40)
IMAGES = [
    {"id": "img-a", "storage_path": "s1/0.jpg"},
    {"id": "img-b", "storage_path": "s1/1.jpg"},
]


def fake(**seed: list[dict[str, Any]]) -> FakeClient:
    return FakeClient({"scan_images": IMAGES, **seed})


def test_run_scan_downloads_every_image_and_finishes_without_the_p2_pipeline() -> None:
    db = fake()
    result = run_scan(cast(Client, db), SCAN)
    assert db.downloaded == ["s1/0.jpg", "s1/1.jpg"]
    assert result.compliance_score == 100
    assert result.words == [] and result.declarations == [] and result.violations == []


def test_run_scan_without_images_fails_loudly() -> None:
    db = FakeClient({"scan_images": []})
    with pytest.raises(ValueError, match="no images"):
        run_scan(cast(Client, db), SCAN)


def test_store_remaps_word_ids_to_the_ids_postgres_assigned() -> None:
    words = [
        Word(id=i, image_id="img-a", text="x", x=0, y=0, w=1, h=1, confidence=0.9) for i in (1, 2)
    ]
    db = fake()
    store(
        cast(Client, db),
        "s1",
        PipelineResult(
            words=words,
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
        ),
    )
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
