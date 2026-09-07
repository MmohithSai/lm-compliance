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


def test_a_wrapped_address_is_one_declaration_not_three() -> None:
    """Real packs wrap the manufacturer over several printed lines. One declaration."""
    got = fields(
        [
            line("MFG BY SOUTH INDIA BOTTLING Co. PVT. LTD., B163-170,", 100, wid=1),
            line("SIPCOT INDL. GROWTH CENTRE, NH7, GANGAIKONDAN VILLAGE,", 134, wid=2),
            line("TIRUNELVELI DIST., TAMILNADU-627352.", 168, wid=3),
        ]
    )
    assert got["manufacturer"] == (
        "MFG BY SOUTH INDIA BOTTLING Co. PVT. LTD., B163-170, "
        "SIPCOT INDL. GROWTH CENTRE, NH7, GANGAIKONDAN VILLAGE, "
        "TIRUNELVELI DIST., TAMILNADU-627352"  # clean() drops the line terminator
    )


def test_absorbing_continuations_stops_at_the_next_anchor() -> None:
    """The line after an address is often the next declaration. It starts its own."""
    got = fields(
        [
            line("MFG BY SOUTH INDIA BOTTLING Co. PVT. LTD.,", 100, wid=1),
            line("TIRUNELVELI DIST., TAMILNADU-627352.", 134, wid=2),
            line("NET QUANTITY: 1 L", 168, wid=3),
        ]
    )
    assert got["manufacturer"] == (
        "MFG BY SOUTH INDIA BOTTLING Co. PVT. LTD., TIRUNELVELI DIST., TAMILNADU-627352"
    )
    assert got["net_quantity"] == "NET QUANTITY: 1 L"


def test_a_far_away_line_is_not_a_continuation() -> None:
    """A whole blank line below means a different part of the panel."""
    got = fields(
        [
            line("Marketed by: Brite Foods Pvt Ltd,", 100, h=30, wid=1),
            line("Plot 12, MIDC, Pune 411019", 134, h=30, wid=2),
            line("KEEP AWAY FROM DIRECT SUNLIGHT", 600, h=30, wid=3),
        ]
    )
    assert got["manufacturer"] == "Marketed by: Brite Foods Pvt Ltd, Plot 12, MIDC, Pune 411019"


def test_an_indented_line_is_not_a_continuation() -> None:
    """A neighbouring column starts at its own left margin; it is not a wrapped line."""
    got = fields(
        [
            line("Marketed by: Brite Foods Pvt Ltd", 100, x=60, w=400, wid=1),
            line("STORE COOL", 130, x=900, w=200, wid=2),
        ]
    )
    assert got["manufacturer"] == "Marketed by: Brite Foods Pvt Ltd"


def test_a_short_value_never_absorbs_the_line_below_it() -> None:
    """Only address blocks wrap. A net quantity that swallowed the next line scored worse."""
    got = fields(
        [
            line("NET QUANTITY: 1 L", 100, h=30, wid=1),
            line("STORE IN A COOL AND DRY PLACE", 134, h=30, wid=2),
        ]
    )
    assert got["net_quantity"] == "NET QUANTITY: 1 L"


def test_origin_alone_is_not_a_country_of_origin() -> None:
    """ "…OF VEGETABLE ORIGIN (472)" is an ingredient, and a bare 'origin' claimed it."""
    got = fields([line("AND EMULSIFIER OF VEGETABLE ORIGIN (472)", 100, wid=1)])
    assert "country_of_origin" not in got


def test_the_value_box_must_share_the_anchors_row_not_just_be_near_it() -> None:
    """Tall OCR boxes made "MRP" on one printed line claim the net weight on the line above."""
    words = [
        line("NET WEIGHT :", 100, x=60, w=300, h=40, wid=1),
        line("25g", 96, x=760, w=120, h=40, wid=2),
        line("MRP", 150, x=60, w=120, h=40, wid=3),
        line("(INCL. OF ALL TAXES) : 5.00", 200, x=60, w=700, h=40, wid=4),
    ]
    got = fields(words)
    assert got["mrp"] == "MRP (INCL. OF ALL TAXES) : 5.00"
    assert got["net_quantity"] == "NET WEIGHT : 25g"


def test_a_bare_anchor_will_not_take_a_box_that_is_a_declaration_itself() -> None:
    """The line under a bare "MRP" is sometimes the next declaration, not its value."""
    got = fields(
        [
            line("MRP", 100, x=60, w=120, h=40, wid=1),
            line("UNIT SALE PRICE : 0.23 PER g", 150, x=60, w=700, h=40, wid=2),
        ]
    )
    assert got.get("mrp") == "MRP"
    assert got["unit_sale_price"] == "UNIT SALE PRICE : 0.23 PER g"


def test_a_box_across_the_panel_is_not_the_value_of_a_bare_anchor() -> None:
    got = fields(
        [
            line("MRP", 100, x=60, w=120, h=40, wid=1),
            line("STORE IN A COOL PLACE", 100, x=1400, w=600, h=40, wid=2),
        ]
    )
    assert got.get("mrp") == "MRP"
