"""The pack's identity: what makes two photographs one product, and what keeps them apart."""

from __future__ import annotations

import pytest

from pipeline.product import company_key, display, match_key, name_key

PARLE = "Mfd by: Parle Products Pvt Ltd, Vile Parle (East), Mumbai 400057"

# The same Reynolds pen, twice. The first is what a person read off the photograph and wrote
# into eval/dataset/phone_reynolds_jetter_classic_ballpen/gold.json; the second is what PP-OCR
# read off scan 3f5b8e1e on the hosted project — no comma after "Limited", and a stray glyph
# glued to "by". One pack, so one product.
REYNOLDS_GOLD = (
    "Manufactured, Marketed and Brand Owned by Reynolds Pens India Private Limited, "
    "Plot No. C-21, SIPCOT Industrial Park, Irungattukottai, Kanchipuram District"
)
REYNOLDS_OCR = (
    "Manufactured,Marketed and Brand Owned bye Reynolds Pens India Private Limited "
    "Plot No. C-21, SlPCOT Industrial Park Irungattukottai, Kanchipuram District"
)


@pytest.mark.parametrize(
    "value",
    [
        PARLE,
        "Manufactured by Parle Products Private Limited, Mumbai - 400057",
        "Marketed by: PARLE PRODUCTS PVT. LTD., Mumbai",
        "Mfd. by:\nParle Products Pvt Ltd,\nMumbai 400 057",
        # The comma the photograph did not print. This is the ordinary case, not the odd one.
        "Mfd by Parle Products Pvt Ltd Vile Parle East Mumbai 400057",
    ],
)
def test_the_same_company_read_five_ways_is_one_key(value: str) -> None:
    """Label, casing, punctuation, the legal form and the commas all vary between two
    photographs of one pack. None of them is the company."""
    assert company_key(value) == "parle products"


def test_a_different_company_is_a_different_key() -> None:
    assert company_key("Mfd by: Britannia Industries Ltd, Bengaluru") == "britannia industries"


def test_a_label_with_a_comma_inside_it_is_still_only_a_label() -> None:
    """The wording "Manufactured,Marketed and Brand Owned by" puts a comma inside the label, so
    cutting at the first comma left the word "Manufactured" and the pack had no identity at all."""
    assert company_key(REYNOLDS_GOLD) == "reynolds pens"
    assert company_key(REYNOLDS_OCR) == "reynolds pens"
    assert display(REYNOLDS_OCR).startswith("Reynolds Pens India Private Limited Plot No. C-21,")


def test_a_declaration_that_is_only_a_label_has_no_company() -> None:
    assert company_key("Manufactured by:") == ""
    assert match_key("Marketed by", "Biscuits") == ""


def test_the_generic_name_loses_its_label_and_keeps_the_rest() -> None:
    assert name_key("Common Name: Biscuits") == "biscuits"
    assert name_key("Generic name - Refined Sunflower Oil") == "refined sunflower oil"


def test_a_pack_with_no_generic_name_still_has_an_identity() -> None:
    """It is the company's unnamed pack, and it must not collide with the company's named ones."""
    assert match_key(PARLE, "") == "parle products|"
    assert match_key(PARLE, "Biscuits") == "parle products|biscuits"


def test_two_products_from_one_company_do_not_share_a_key() -> None:
    assert match_key(PARLE, "Biscuits") != match_key(PARLE, "Rusk")


def test_display_drops_the_label_and_keeps_the_pack_s_own_spelling() -> None:
    assert display(PARLE) == "Parle Products Pvt Ltd, Vile Parle (East), Mumbai 400057"
    assert display("Common Name: Biscuits") == "Biscuits"
