"""`applies_to` filtering in run_rules. This part of the engine exists today, so no xfail."""

from __future__ import annotations

from pipeline.models import Severity, Source
from pipeline.rules_engine import applicable_rules

from .helpers import RULES, ctx, decl, good, ids, one, run, without


def test_d7_not_imported_not_applicable() -> None:
    assert ids(run(good(), only="D7")) == []


def test_e1_not_applied_to_packages() -> None:
    assert ids(run(without(good(), "net_quantity"), ctx(source=Source.package), only="E1")) == []


def test_e2_not_applied_to_packages() -> None:
    assert ids(run(good(), ctx(source=Source.package, is_imported=True), only="E2")) == []


def test_package_rules_are_not_applied_to_a_listing() -> None:
    """A screenshot is not the package: what is printed on it is not in the frame. Rule 6(10)
    is the whole check on an e-commerce scan, which is also how eval/dataset gold is written."""
    bare = [decl("generic_name", "Biscuits")]
    assert ids(run(bare, ctx(source=Source.ecommerce))) == ["E1"]
    assert ids(run(bare, ctx(source=Source.package))) != ["E1"]


# ---------------------------------------------------------------- P8: what a listing is spared

# Everything read off the pixels of a real pack: print height, character width, contrast, which
# panel a declaration sits on, and whether it is on a bottom or a seam. A screenshot has none of
# those in the frame, and a scale measured on one would be measuring the screen.
PHYSICAL_ONLY = {"F1", "F2", "F3", "P1", "P2", "P3"}


def test_no_physical_check_is_ever_applied_to_a_listing() -> None:
    """Not failed, not "unverifiable" — never applied. Both would put a font finding on the
    report for a screenshot, and the second reads as "we tried and could not"."""
    listing = ctx(source=Source.ecommerce, has_reference_card=True, mm_per_px=0.125)
    applied = {r.rule_id for r in applicable_rules(good(), listing, RULES)}
    assert applied & PHYSICAL_ONLY == set()
    assert applied <= {"E1", "E2"}
    assert ids(run(good(), listing)) == []


def test_the_same_declarations_on_a_pack_do_reach_those_checks() -> None:
    """The other half of the pin: PHYSICAL_ONLY is excluded because of the source and not
    because the rules stopped applying to everything."""
    applied = {r.rule_id for r in applicable_rules(good(), ctx(source=Source.package), RULES)}
    assert PHYSICAL_ONLY - {"F3"} <= applied


def test_a_real_listing_missing_its_consumer_care_is_a_rule_6_10_violation() -> None:
    """The declarations eval/dataset/ecom_amazon_tata_salt_1kg/gold.json holds, read off the
    Amazon listing by hand. Its gold verdict is exactly ["E1"]."""
    listing = [
        decl("generic_name", "Generic Name : Salt"),
        decl("manufacturer", "Manufacturer : Tata Chemicals Limited, P. 0. Mithapur-361 345"),
        decl("net_quantity", "Net Quantity : 1000.0 Grams"),
        decl("mrp", "M.R.P.: Rs 32.00"),
        decl("unit_sale_price", "Rs 2.90 /100 g"),
    ]
    found = run(listing, ctx(source=Source.ecommerce))
    assert ids(found) == ["E1"]
    e1 = one(found, "E1")
    assert e1.rule_ref == "Rule 6(10)"
    assert e1.severity is Severity.critical
    assert e1.evidence.values == {"missing": "consumer_care"}
    assert "consumer_care" in e1.message
