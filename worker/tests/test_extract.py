"""Anchor precedence and the layout fallback. OCR quality itself is measured by the eval."""

from __future__ import annotations

from pipeline.extractors.regex_layout import RegexLayoutExtractor
from pipeline.models import Declaration, ScanContext, Word

EXTRACT = RegexLayoutExtractor()


def line(text: str, y: int, x: int = 60, w: int = 500, h: int = 30, wid: int = 0) -> Word:
    return Word(id=wid, image_id="front", text=text, x=x, y=y, w=w, h=h, confidence=0.98)


def fields(words: list[Word]) -> dict[str, str]:
    decls: list[Declaration] = EXTRACT.extract(words, ScanContext())
    return {d.field: d.value for d in decls}


def test_one_line_per_declaration_keeps_the_whole_printed_line() -> None:
    got = fields(
        [
            line("BRITE BISCUITS", 60, wid=0),
            line("Net Qty: 200 g", 160, wid=1),
            line("MRP 20.00 (Inclusive of all taxes)", 230, wid=2),
        ]
    )
    assert got == {
        "net_quantity": "Net Qty: 200 g",
        "mrp": "MRP 20.00 (Inclusive of all taxes)",
    }, "a header with no anchor must claim nothing"


def test_the_longest_anchor_wins_so_mfd_by_is_the_manufacturer_not_the_date() -> None:
    got = fields(
        [line("Mfd by: Brite Foods Pvt Ltd, Pune", 160, wid=1), line("Mfd: 03/2026", 230, wid=2)]
    )
    assert got == {"manufacturer": "Mfd by: Brite Foods Pvt Ltd, Pune", "mfg_date": "Mfd: 03/2026"}


def test_a_bare_anchor_takes_the_box_to_its_right_then_the_one_below() -> None:
    words = [
        line("MRP", 160, x=60, w=60, wid=1),
        line("Rs 20.00", 158, x=140, w=140, wid=2),
        line("Best before", 230, x=60, w=200, wid=3),
        line("6 months from packaging", 270, x=60, w=400, wid=4),
    ]
    got = fields(words)
    assert got["mrp"] == "MRP Rs 20.00"
    assert got["best_before"] == "Best before 6 months from packaging"
    mrp = [d for d in EXTRACT.extract(words, ScanContext()) if d.field == "mrp"]
    assert mrp[0].word_ids == [1, 2]


def test_the_first_box_in_reading_order_wins_a_repeated_anchor() -> None:
    got = fields([line("MRP 20.00", 300, wid=1), line("MRP 99.00", 160, wid=2)])
    assert got == {"mrp": "MRP 99.00"}
