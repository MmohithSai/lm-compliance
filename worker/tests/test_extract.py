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
    """The line under a bare "MRP" is sometimes the next declaration, not its value.

    Nothing else on this panel carries a figure, so there is no price here to report.
    """
    got = fields(
        [
            line("MRP", 100, x=60, w=120, h=40, wid=1),
            line("UNIT SALE PRICE : 0.23 PER g", 150, x=60, w=700, h=40, wid=2),
        ]
    )
    assert "mrp" not in got
    assert got["unit_sale_price"] == "UNIT SALE PRICE : 0.23 PER g"


def test_a_box_across_the_panel_is_not_the_value_of_a_bare_anchor() -> None:
    got = fields(
        [
            line("Made in", 100, x=60, w=200, h=40, wid=1),
            line("SPAIN", 100, x=1400, w=300, h=40, wid=2),
        ]
    )
    assert got["country_of_origin"] == "Made in"


def test_an_anchor_still_counts_when_ocr_glues_the_value_to_it() -> None:
    """PP-OCR reads "UNIT SALE PRICE : ₹ 0.20 PER g" as one run with the space missing."""
    got = fields([line("UNIT SALE PRICE0.20PER g", 100, wid=1)])
    assert got["unit_sale_price"] == "UNIT SALE PRICE0.20PER g"


def test_a_glued_letter_is_still_a_different_word() -> None:
    """'exp' must not claim 'export', or every export declaration becomes a best-before."""
    got = fields([line("EXPORT QUALITY", 100, wid=1)])
    assert "best_before" not in got


def test_a_price_label_pointing_somewhere_else_is_not_a_price() -> None:
    """Bottles print "MRP (INCL OF ALL TAXES): SEE BOTTLE". There is no price on that panel."""
    got = fields([line("MRP (INCL OF ALL TAXES): SEE BOTTLE", 100, wid=1)])
    assert "mrp" not in got


def test_a_price_label_finds_the_number_printed_under_it() -> None:
    got = fields(
        [
            line("MRP (Inclusive of all taxes)", 100, x=60, w=500, h=40, wid=1),
            line("486.00 (Rs. 4.86/ml)", 150, x=60, w=500, h=40, wid=2),
        ]
    )
    assert got["mrp"] == "MRP (Inclusive of all taxes) 486.00 (Rs. 4.86/ml)"


def test_a_quantity_label_skips_a_neighbour_with_no_number_in_it() -> None:
    """ "Net Content:" took "COOL. STOR" off the storage line printed beside it."""
    got = fields(
        [
            line("Net Content:", 100, x=60, w=300, h=40, wid=1),
            line("COOL.STOR", 100, x=380, w=200, h=40, wid=2),
            line("500 mL", 150, x=60, w=200, h=40, wid=3),
        ]
    )
    assert got["net_quantity"] == "Net Content: 500 mL"


def test_a_line_that_points_somewhere_else_is_not_the_declaration() -> None:
    """Packs cross-refer constantly. "ADDRESS: SAME AS MKT BY ADDRESS" is not the address."""
    got = fields(
        [
            line("ADDRESS: SAME AS MKT BY ADDRESS", 100, wid=1),
            line("MKT BY: Brite Foods Pvt Ltd, Pune 411019", 400, wid=2),
        ]
    )
    assert got["manufacturer"] == "MKT BY: Brite Foods Pvt Ltd, Pune 411019"


def test_see_the_neck_is_not_a_date() -> None:
    got = fields([line("FOR DATE OF MANUFACTURE & BATCH NO.: SEE NECK", 100, wid=1)])
    assert "mfg_date" not in got


def test_a_wrapped_address_stops_at_a_line_that_points_somewhere_else() -> None:
    """Kurkure prints "For Mkt. address, scan barcode" under "MARKETED BY:".

    That line is a pointer, not the address, and the block has to stop at it.
    """
    got = fields(
        [
            line("MARKETED BY:", 100, x=60, w=300, h=34, wid=1),
            line("PepsiCo India Holdings Pvt. Ltd.", 140, x=60, w=600, h=34, wid=2),
            line("For Mkt. address, scan barcode", 180, x=60, w=600, h=34, wid=3),
            line("For feedback or queries write to:", 220, x=60, w=600, h=34, wid=4),
        ]
    )
    assert got["manufacturer"] == "MARKETED BY: PepsiCo India Holdings Pvt. Ltd"


def test_a_table_cell_value_is_found_even_when_it_sits_off_the_labels_row() -> None:
    """The pixels are the Reynolds pen box in eval/dataset, rounded: a bordered table whose
    label cell wraps onto a second line, so the value is centred against both lines and misses
    the anchor's own row by two pixels. Widening the row test was measured twice and cost real
    accuracy both times, so the reach into the cell runs only after everything else has failed.
    """
    got = fields(
        [
            line("MRP", 502, x=395, w=55, h=31, wid=0),
            line("25.00", 514, x=563, w=84, h=42, wid=1),
            line("(incl.of all taxes", 530, x=396, w=149, h=34, wid=2),
            line("Month&Year", 572, x=395, w=145, h=28, wid=3),
            line("02/2026", 583, x=571, w=105, h=29, wid=4),
            line("of Manufacture", 598, x=395, w=163, h=29, wid=5),
        ]
    )
    assert got["mrp"] == "MRP (incl.of all taxes 25.00", "the tax wording is part of the label cell"
    assert got["mfg_date"] == "Month&Year of Manufacture 02/2026"


def test_the_next_row_of_a_table_is_not_part_of_the_label_cell() -> None:
    """The guard on the test above: without it "MRP" swallows the row printed under it."""
    got = fields(
        [
            line("MRP", 502, x=395, w=55, h=31, wid=0),
            line("25.00", 514, x=563, w=84, h=42, wid=1),
            line("Batch", 560, x=396, w=149, h=34, wid=2),
        ]
    )
    assert got["mrp"] == "MRP 25.00"
