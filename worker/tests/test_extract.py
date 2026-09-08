"""Anchor precedence and the layout fallback. OCR quality itself is measured by the eval."""

from __future__ import annotations

from pipeline.extractors.regex_layout import RegexLayoutExtractor
from pipeline.models import Declaration, ScanContext, Source, Word

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


def test_reading_order_across_photographs_is_the_order_they_were_handed_in() -> None:
    """On a real scan `image_id` is a uuid. Sorting on it put the photographs in a random order
    and decided which of two prices the report quoted; the eval never saw it because there the
    id is a file name that happens to sort like the upload. The first photograph given is the
    first read, whatever its id says."""
    first = line("MRP 20.00", 100, wid=0).model_copy(update={"image_id": "zzz-second-by-name"})
    second = line("MRP 99.00", 100, wid=1).model_copy(update={"image_id": "aaa-first-by-name"})
    assert fields([first, second]) == {"mrp": "MRP 20.00"}
    assert fields([second, first]) == {"mrp": "MRP 99.00"}


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
    """And a bare "Made in" with nothing beside it is no declaration at all: the label names
    one without carrying one, the same as "MRP" over "SEE BOTTLE"."""
    got = fields(
        [
            line("Made in", 100, x=60, w=200, h=40, wid=1),
            line("SPAIN", 100, x=1400, w=300, h=40, wid=2),
        ]
    )
    assert "country_of_origin" not in got


# ---------------------------------------------------------------- OCR drops spaces


def test_an_anchor_still_counts_when_ocr_glues_a_word_to_its_front() -> None:
    """The Bisleri bottle: "CONTACT: CUSTOMER CARE EXECUTIVE" came back as one run of letters,
    and a word boundary before "customer" refused the whole consumer care block."""
    got = fields(
        [
            line("CONTACICUSTOMER CARE EXECUTIVE C1800-121-1007", 873, x=48, w=1271, h=121, wid=1),
            line("EMAILWECARE@BISLERI.CO.IN", 988, x=57, w=715, h=67, wid=2),
        ]
    )
    assert got["consumer_care"].startswith("CONTACICUSTOMER CARE EXECUTIVE")


def test_an_anchor_still_counts_when_ocr_glues_its_own_words_together() -> None:
    assert fields([line("MADEIN INDIA", 100, wid=1)]) == {"country_of_origin": "MADEIN INDIA"}
    got = fields([line("DATE OFMFG: 10/12/2024", 100, wid=1)])
    assert got == {"mfg_date": "DATE OFMFG: 10/12/2024"}


def test_a_short_anchor_keeps_its_word_boundary() -> None:
    """The glue tolerance is for long anchors. "made in" inside "homemade indian" is not a
    country of origin, and "exp" inside "export" is not a date."""
    assert fields([line("HOMEMADE INDIAN SNACKS", 100, wid=1)]) == {}


def test_usp_at_the_start_of_the_box_is_the_unit_sale_price() -> None:
    assert fields([line("(USP0.20/-perg)", 100, wid=1)]) == {"unit_sale_price": "(USP0.20/-perg)"}
    # ...and in the middle of a pointer's list it is not
    assert "unit_sale_price" not in fields(
        [line("FOR DATE OF MANUFACTURE, USE BY, BATCH NO., USP AND", 100, wid=1)]
    )


def test_an_email_address_is_one_word_and_never_a_label() -> None:
    """The glued-prefix tolerance must not find "consumer care" inside
    "reynoldsindiaconsumercare@newellco.com": read as a label, the e-mail line stopped the
    consumer care block just short of the e-mail D6 asks for."""
    got = fields(
        [
            line(
                "Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348",
                100,
                wid=1,
            ),
            line("E-mail: reynoldsindiaconsumercare@newellco.com", 134, wid=2),
        ]
    )
    assert got["consumer_care"].endswith("reynoldsindiaconsumercare@newellco.com")


def test_the_fuller_label_beats_a_bare_noun_that_came_first() -> None:
    """Amazon's buy box prints "Quantity: 1" above the product table's "Net Quantity : 800.0
    Grams". The bare noun is a label; the legal wording is the declaration."""
    got = fields([line("Quantity:1", 100, wid=1), line("Net Quantity : 800.0 Grams", 900, wid=2)])
    assert got == {"net_quantity": "Net Quantity : 800.0 Grams"}


def test_the_fullest_address_block_wins_whichever_photograph_came_first() -> None:
    """The amazon.in Tata Salt listing names the maker twice: "Manufacturer : Tata Sampann" in
    the bullet list and the full address in the product table. The address is the declaration
    D1 judges, and the answer must not depend on the order the tiles were uploaded in."""
    short = line("Manufacturer : Tata Sampann", 100, wid=1).model_copy(update={"image_id": "a"})
    full = line(
        "Manufacturer : Tata Chemicals Limited, P.O. Mithapur-361 345, Gujarat", 100, wid=2
    ).model_copy(update={"image_id": "b"})
    want = {"manufacturer": full.text}
    assert fields([short, full]) == want
    assert fields([full, short]) == want


def test_an_address_beats_a_bare_name_and_the_answer_does_not_depend_on_order() -> None:
    """The Pepsi bottle names its manufacturer and, further along, its marketer, and neither
    block carries an address; D1 fails on both. Whichever is chosen, it is the same one from
    either order — and a block that does carry an address beats both."""
    mfd = line("MFD.BY:VARUN BEVERAGESLIMITED", 610, x=825, w=265, h=32, wid=1)
    mkt = line("MKT.BY. PEPSICO INDIA HOLDINGS PVL.LID", 685, x=1277, w=236, h=39, wid=2)
    assert fields([mfd, mkt]) == fields([mkt, mfd])
    full = line("MKT BY: Brite Foods Pvt Ltd, Plot 12, MIDC, Pune 411019", 900, x=825, wid=3)
    assert fields([mkt, full, mfd])["manufacturer"] == full.text
    assert fields([full, mkt, mfd])["manufacturer"] == full.text


def test_a_label_box_already_read_is_not_read_again_in_a_later_pass() -> None:
    """The Kurkure pack: "MARKETED BY:" found its value in the first pass, and revisited in
    the table pass with that value out of reach it took the FSSAI logo line instead."""
    got = fields(
        [
            line("MARKETED BY:", 563, x=1038, w=186, h=39, wid=1),
            line("PepsiCo India Holdings Pvt.Ltd", 595, x=1040, w=360, h=47, wid=2),
            line("fssat", 634, x=1110, w=170, h=91, wid=3),
            line(
                "For feedback or queries write indicating Batch No.and",
                805,
                x=1053,
                w=440,
                h=38,
                wid=4,
            ),
        ]
    )
    assert got["manufacturer"] == "MARKETED BY: PepsiCo India Holdings Pvt.Ltd"


def test_a_listing_s_quantity_row_is_the_net_quantity() -> None:
    """Flipkart labels the row "Quantity" with the figure under it; a water bottle's "ADDED
    QUANTITY PER 100 ml" starts with another word and is not one."""
    got = fields(
        [
            line("Quantity", 453, x=761, w=60, h=22, wid=1),
            line("1000 g", 471, x=763, w=53, h=24, wid=2),
        ]
    )
    assert got == {"net_quantity": "Quantity 1000 g"}
    assert "net_quantity" not in fields([line("ADDED QUANTITY PER 100 ml", 100, wid=1)])


# ---------------------------------------------------------------- the figure has a shape


def test_a_batch_code_beside_mrp_is_not_the_price() -> None:
    """The Ching's soy sauce in eval/dataset: the value column sits half a line below the label
    column, so the batch code is the box nearest "MRP:" — and the price is one line down."""
    got = fields(
        [
            line("BATCH NO:", 774, x=202, w=165, h=43, wid=1),
            line("AA4L10002502)", 796, x=443, w=285, h=46, wid=2),
            line("MRP:", 808, x=207, w=104, h=39, wid=3),
            line("25Rs.0.28/9)", 829, x=444, w=264, h=50, wid=4),
        ]
    )
    assert got.get("mrp", "") != "MRP: AA4L10002502)"


def test_a_price_beside_use_by_is_not_the_date() -> None:
    got = fields(
        [
            line("USE BY:", 1173, x=101, w=201, h=90, wid=1),
            line("79/-", 1195, x=716, w=152, h=98, wid=2),
        ]
    )
    assert "best_before" not in got


def test_a_licence_number_is_not_a_month_and_year() -> None:
    assert "mfg_date" not in fields([line("Mfg Licno.:DNH/C/18", 100, wid=1)])


def test_best_before_in_months_needs_no_figure() -> None:
    got = fields([line("BEST BEFORE SIX MONTHS FROM MANUFACTURE", 100, wid=1)])
    assert got["best_before"] == "BEST BEFORE SIX MONTHS FROM MANUFACTURE"


def test_a_price_glued_to_its_label_is_still_a_price() -> None:
    assert fields([line("M.R.P10.00", 100, wid=1)]) == {"mrp": "M.R.P10.00"}


def test_a_two_line_label_finds_its_figure_beside_the_second_line() -> None:
    """The Balaji wafers: "MRP" over "(INCL. OF ALL TAXES)", and "5.00" level with the second
    line of the label, off the first line's row by a full line."""
    got = fields(
        [
            line("NET WEIGHT:", 1270, x=14, w=223, h=80, wid=1),
            line("25g", 1300, x=454, w=98, h=90, wid=2),
            line("MRP", 1367, x=9, w=126, h=79, wid=3),
            line("(INCL.OF ALL TAXES)", 1441, x=17, w=343, h=96, wid=4),
            line("5.00", 1451, x=558, w=108, h=82, wid=5),
            line("UNIT SALE PRIE3020DC", 1512, x=14, w=475, h=87, wid=6),
        ]
    )
    assert got["mrp"] == "MRP (INCL.OF ALL TAXES) 5.00"
    assert got["net_quantity"] == "NET WEIGHT: 25g"


def test_a_figure_on_the_next_line_in_the_value_column_is_found() -> None:
    """The Cetaphil lotion: the price is printed a line below its label and indented to the
    value column, and the packing code on the label's own row is not a price."""
    got = fields(
        [
            line("MRP (Inclusive of all taxes)", 1024, x=204, w=215, h=52, wid=1),
            line("FIL1745.V00", 1022, x=1019, w=99, h=41, wid=2),
            line("486.00Rs.4.86/ml", 1134, x=481, w=546, h=82, wid=3),
        ]
    )
    assert got["mrp"] == "MRP (Inclusive of all taxes) 486.00Rs.4.86/ml"


def test_a_date_a_full_line_off_its_label_is_taken_when_it_is_the_only_date_in_reach() -> None:
    """The Quaker oats, photographed at an angle: the value column sits a line above the label
    column. The relaxed reach is only open to a box of the right shape."""
    got = fields(
        [
            line("MFD:", 1022, x=94, w=139, h=88, wid=1),
            line("06SEP23", 960, x=620, w=306, h=129, wid=2),
            line("05SEP24", 1074, x=618, w=310, h=135, wid=3),
            line("USE BY:", 1173, x=101, w=201, h=90, wid=4),
            line("79/-", 1195, x=716, w=152, h=98, wid=5),
        ]
    )
    assert got["mfg_date"] == "MFD: 06SEP23"
    assert got["best_before"] == "USE BY: 05SEP24"


def test_a_barcode_line_under_mrp_is_not_the_price() -> None:
    """The Kissan jam: with a little slack for padded boxes, the line under "MRP (INCL. OF ALL
    TAXES)" was the barcode, and a D5 the pack really fails turned into a pass."""
    got = fields(
        [
            line("MRP  (INCL.OF ALL TAXES)", 100, x=60, w=500, h=40, wid=1),
            line("69725945 JAM.INGREDIENTS:SUGAR 8901030922787>", 136, x=60, w=900, h=40, wid=2),
        ]
    )
    assert "mrp" not in got


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


def test_the_licence_number_under_an_address_is_not_part_of_it() -> None:
    """The Kurkure pack, as PP-OCR read it: the FSSAI logo comes back as "fssat", the licence
    number follows, and neither is the maker's address."""
    got = fields(
        [
            line("MARKETED BY:", 563, x=1038, w=186, h=39, wid=1),
            line("PepsiCo India Holdings Pvt.Ltd", 595, x=1040, w=360, h=47, wid=2),
            line("fssat", 634, x=1110, w=170, h=91, wid=3),
            line("Lic.No.10014064000435", 716, x=1055, w=257, h=43, wid=4),
        ]
    )
    assert got["manufacturer"] == "MARKETED BY: PepsiCo India Holdings Pvt.Ltd"


def test_a_storage_instruction_under_a_care_block_is_not_part_of_it() -> None:
    got = fields(
        [
            line("CONTACT CUSTOMER SERVICE MANAGER", 743, x=685, w=484, h=56, wid=1),
            line("AT:P.O.BOX 27DLF QUTAB ENCLAVE-1,", 793, x=691, w=473, h=52, wid=2),
            line("CONSUMER.FEEDBACK@PEPSICO.COM", 883, x=673, w=507, h=57, wid=3),
            line(
                "KEEP IN COOL AND DRY PLACE AWAY FROM DIRECT SUNLIGHT",
                988,
                x=672,
                w=423,
                h=34,
                wid=4,
            ),
        ]
    )
    assert got["consumer_care"] == (
        "CONTACT CUSTOMER SERVICE MANAGER AT:P.O.BOX 27DLF QUTAB ENCLAVE-1, "
        "CONSUMER.FEEDBACK@PEPSICO.COM"
    )


def test_a_care_block_keeps_its_address_by_reference() -> None:
    """The Bisleri bottle. Rule 6(2) wants an address, and "same as the marketer's" is one, even
    though the line holds a maker's anchor and a pointer. On the Reynolds pen the same line
    comes second of four ("at the above address.") and the phone and e-mail follow it."""
    got = fields(
        [
            line("CONTACT: CUSTOMER CARE EXECUTIVE 1800-121-1007", 873, x=48, w=1271, h=121, wid=1),
            line("EMAIL: WECARE@BISLERI.CO.IN", 988, x=57, w=715, h=67, wid=2),
            line("ADDRESS: SAME AS MKT BY ADDRESS", 1065, x=56, w=746, h=87, wid=3),
        ]
    )
    assert got["consumer_care"] == (
        "CONTACT: CUSTOMER CARE EXECUTIVE 1800-121-1007 EMAIL: WECARE@BISLERI.CO.IN "
        "ADDRESS: SAME AS MKT BY ADDRESS"
    )
    got = fields(
        [
            line("Consumer Care Officer", 100, wid=1),
            line("at the above address.", 134, wid=2),
            line("Toll Free No.: 0008 0005 04348", 168, wid=3),
            line("E-mail: care@example.com", 202, wid=4),
        ]
    )
    assert got["consumer_care"].endswith("0008 0005 04348 E-mail: care@example.com")


def test_a_maker_s_block_still_stops_before_an_address_by_reference() -> None:
    got = fields(
        [
            line("MKT BY: Brite Foods Pvt Ltd, Pune 411019", 100, wid=1),
            line("ADDRESS: SAME AS ABOVE", 134, wid=2),
        ]
    )
    assert got["manufacturer"] == "MKT BY: Brite Foods Pvt Ltd, Pune 411019"


# ------------------------------------------------- P6: a listing labels it "Manufacturer"


def test_a_bare_manufacturer_label_is_the_maker() -> None:
    """Every e-commerce listing writes it this way, and so do packs that set their declarations
    in a table. "manufactured by" and "importer" were anchors; this one was the oversight."""
    assert fields([line("Manufacturer : Parle Biscuits Pvt Ltd", 160, wid=1)]) == {
        "manufacturer": "Manufacturer : Parle Biscuits Pvt Ltd"
    }


def test_the_word_manufacturer_inside_a_line_is_not_a_label() -> None:
    """Both of these stand above the real row on the amazon.in Tata Salt listing, and first box
    in reading order wins, so either one shadowed the declaration itself."""
    words = [
        line("From the manufacturer", 60, wid=0),
        line("Is Discontinued By Manufacturer : No", 120, wid=1),
        line("Manufacturer : Tata Chemicals Limited", 180, wid=2),
    ]
    assert fields(words) == {"manufacturer": "Manufacturer : Tata Chemicals Limited"}


def test_a_screenshot_does_not_wrap_an_address_into_the_next_row() -> None:
    """On a pack the line under an address is the rest of it. On a listing it is the next row of
    the specification table, and swallowing it lost both declarations."""
    words = [
        line("Manufacturer : Parle Biscuits Pvt Ltd", 160, wid=0),
        line("ASIN B0754HP7X2", 200, wid=1),
    ]
    decls = EXTRACT.extract(words, ScanContext(source=Source.ecommerce))
    assert [d.value for d in decls] == ["Manufacturer : Parle Biscuits Pvt Ltd"]


# ---------------------------------------------------------------- P8: page furniture is not a
# declaration


def listing(words: list[Word]) -> dict[str, str]:
    decls = EXTRACT.extract(words, ScanContext(source=Source.ecommerce))
    return {d.field: d.value for d in decls}


def test_the_amazon_navigation_bar_is_not_a_consumer_care_declaration() -> None:
    """ "Customer Service New Releases" sits above every Amazon listing. Claimed as the consumer
    care declaration it made Rule 6(10) find the field present, and three real listings that
    gold marks E1 scored 100 out of 100."""
    assert "consumer_care" not in listing([line("Customer Service New Releases", 20, wid=0)])


def test_a_real_care_line_further_down_the_page_still_wins_the_field() -> None:
    """Skipping the box, rather than claiming it and stopping, is what makes this safe."""
    got = listing(
        [
            line("Customer Service New Releases", 20, wid=0),
            line("Customer care: Brite Foods, Pune, 1800-123-4567", 900, wid=1),
        ]
    )
    assert got["consumer_care"] == "Customer care: Brite Foods, Pune, 1800-123-4567"


def test_a_care_line_with_only_an_email_is_still_a_declaration() -> None:
    """A telephone number or an e-mail address — either is a way to reach the seller, and a pack
    that prints one and loses the other to OCR must not lose the whole declaration."""
    got = fields([line("Consumer care: Brite Foods, Pune; care@britefoods.in", 160, wid=1)])
    assert got["consumer_care"] == "Consumer care: Brite Foods, Pune; care@britefoods.in"


def test_a_care_heading_with_no_contact_under_it_claims_nothing() -> None:
    assert "consumer_care" not in fields([line("Consumer complaints", 160, wid=1)])
