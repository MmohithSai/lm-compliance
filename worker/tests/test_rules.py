"""Behaviour of every rule in rules/pc_rules_2011.yaml: pass, fail and edge cases.

Written before the engine (P3). Delete the xfail line below when CHECKS are filled in; strict
mode makes the suite fail the moment the checks start passing, so it cannot be forgotten.
"""

from __future__ import annotations

import pytest

from pipeline.models import CheckStatus, ScaleSource, Severity, Source

from .helpers import ctx, decl, good, ids, one, replace, run, without

pytestmark = pytest.mark.xfail(
    strict=True, raises=NotImplementedError, reason="P3: rule engine not built yet"
)

# ---------------------------------------------------------------- D1 manufacturer


def test_d1_pass() -> None:
    assert ids(run(good(), only="D1")) == []


def test_d1_missing_is_critical() -> None:
    v = one(run(without(good(), "manufacturer"), only="D1"), "D1")
    assert v.severity == Severity.critical
    assert v.rule_ref == "Rule 6(1)(a)"


def test_d1_name_without_address_fails() -> None:
    assert ids(run(replace(good(), "manufacturer", "Parle"), only="D1")) == ["D1"]


def test_d1_importer_alone_satisfies() -> None:
    decls = without(good(), "manufacturer") + [
        decl("importer", "XYZ Imports Pvt Ltd, 12 MG Road, Bengaluru 560001")
    ]
    assert ids(run(decls, only="D1")) == []


# ---------------------------------------------------------------- D2 generic name


def test_d2_pass() -> None:
    assert ids(run(good(), only="D2")) == []


def test_d2_missing_is_major() -> None:
    assert one(run(without(good(), "generic_name"), only="D2"), "D2").severity == Severity.major


def test_d2_empty_value_fails() -> None:
    assert ids(run(replace(good(), "generic_name", "   "), only="D2")) == ["D2"]


# ---------------------------------------------------------------- D3 net quantity


@pytest.mark.parametrize(
    "value",
    ["Net Qty: 200 g", "500 ML", "12 pcs", "1.5 L", "2 N", "Net Wt. 100g", "10 kg", "2 x 100 g"],
)
def test_d3_standard_units_pass(value: str) -> None:
    assert ids(run(replace(good(), "net_quantity", value), only="D3")) == []


@pytest.mark.parametrize(
    "value", ["approx 500 g", "about 1 kg", "500 gms", "500", "1 dozen", "Net Qty: approx. 200g"]
)
def test_d3_bad_values_fail(value: str) -> None:
    v = one(run(replace(good(), "net_quantity", value), only="D3"), "D3")
    assert v.severity == Severity.critical
    assert v.evidence.values.get("net_quantity") == value


def test_d3_missing_fails() -> None:
    assert ids(run(without(good(), "net_quantity"), only="D3")) == ["D3"]


# ---------------------------------------------------------------- D4 month + year


@pytest.mark.parametrize(
    "value", ["Mfd: 03/2026", "March 2026", "2026-03", "Pkd 09/2026", "MFG 08.2026"]
)
def test_d4_valid_dates_pass(value: str) -> None:
    assert ids(run(replace(good(), "mfg_date", value), only="D4")) == []


@pytest.mark.parametrize("value", ["12/2027", "13/2026", "Mfd: soon", "10/2026"])
def test_d4_future_or_unreadable_fail(value: str) -> None:
    assert one(run(replace(good(), "mfg_date", value), only="D4"), "D4").severity == Severity.major


def test_d4_missing_fails() -> None:
    assert ids(run(without(good(), "mfg_date"), only="D4")) == ["D4"]


# ---------------------------------------------------------------- D5 MRP wording


@pytest.mark.parametrize(
    "value",
    [
        "MRP ₹20.00 (Inclusive of all taxes)",
        "M.R.P. Rs.20/- (Incl. of all taxes)",
        "Maximum Retail Price Rs 20 inclusive of all taxes",
        "MRP Rs. 1,250.00 Inclusive of all taxes",
    ],
)
def test_d5_valid_mrp_pass(value: str) -> None:
    assert ids(run(replace(good(), "mrp", value), only="D5")) == []


@pytest.mark.parametrize(
    "value",
    [
        "Price Rs 20 inclusive of all taxes",  # no MRP wording
        "MRP Rs 20",  # no inclusive of all taxes
        "MRP inclusive of all taxes",  # no amount
        "MRP 20 inclusive of all taxes",  # no rupee sign
    ],
)
def test_d5_bad_mrp_fail(value: str) -> None:
    assert one(run(replace(good(), "mrp", value), only="D5"), "D5").severity == Severity.critical


def test_d5_missing_fails() -> None:
    assert ids(run(without(good(), "mrp"), only="D5")) == ["D5"]


# ---------------------------------------------------------------- D5b single MRP


def test_d5b_one_mrp_pass() -> None:
    assert ids(run(good(), only="D5b")) == []


def test_d5b_two_different_mrps_fail() -> None:
    decls = good() + [decl("mrp", "MRP ₹25.00 Inclusive of all taxes", image_id="img2")]
    v = one(run(decls, only="D5b"), "D5b")
    assert v.severity == Severity.critical
    assert "20" in v.message and "25" in v.message


def test_d5b_same_mrp_twice_is_fine() -> None:
    decls = good() + [decl("mrp", "MRP ₹20.00 (Inclusive of all taxes)", image_id="img2")]
    assert ids(run(decls, only="D5b")) == []


# ---------------------------------------------------------------- D6 consumer care


@pytest.mark.parametrize(
    "value",
    [
        "Consumer care: Parle, Mumbai; 1800-123-4567; care@parle.com",
        "care@parle.com +91 22 1234 5678",
        "Customer care: 022-12345678, email: help@brand.in",
    ],
)
def test_d6_valid_pass(value: str) -> None:
    assert ids(run(replace(good(), "consumer_care", value), only="D6")) == []


@pytest.mark.parametrize("value", ["care@parle.com", "1800-123-4567", "Parle Products, Mumbai"])
def test_d6_missing_phone_or_email_fail(value: str) -> None:
    assert (
        one(run(replace(good(), "consumer_care", value), only="D6"), "D6").severity
        == Severity.major
    )


def test_d6_missing_fails() -> None:
    assert ids(run(without(good(), "consumer_care"), only="D6")) == ["D6"]


# ---------------------------------------------------------------- D7 country of origin


def test_d7_imported_with_origin_pass() -> None:
    decls = good() + [decl("country_of_origin", "Made in Thailand")]
    assert ids(run(decls, ctx(is_imported=True), only="D7")) == []


def test_d7_imported_without_origin_is_critical() -> None:
    v = one(run(good(), ctx(is_imported=True), only="D7"), "D7")
    assert v.severity == Severity.critical
    assert v.rule_ref == "Rule 6(1)(aa)"


def test_d7_importer_declaration_implies_imported() -> None:
    decls = good() + [decl("importer", "XYZ Imports Pvt Ltd, 12 MG Road, Bengaluru 560001")]
    assert ids(run(decls, only="D7")) == ["D7"]


# ---------------------------------------------------------------- D8 unit sale price (minor)


def test_d8_present_pass() -> None:
    assert ids(run(good(), only="D8")) == []


def test_d8_missing_is_minor() -> None:
    assert one(run(without(good(), "unit_sale_price"), only="D8"), "D8").severity == Severity.minor


def test_d8_empty_value_fails() -> None:
    assert ids(run(replace(good(), "unit_sale_price", ""), only="D8")) == ["D8"]


# ---------------------------------------------------------------- D9 best before (info)


def test_d9_present_pass() -> None:
    assert ids(run(good(), only="D9")) == []


def test_d9_missing_is_info() -> None:
    assert one(run(without(good(), "best_before"), only="D9"), "D9").severity == Severity.info


def test_d9_use_by_counts() -> None:
    assert ids(run(replace(good(), "best_before", "Use by 12/2026"), only="D9")) == []


# ---------------------------------------------------------------- F1 font height (Table I)


def _sized(height_mm: float) -> list:  # type: ignore[type-arg]
    return [d.model_copy(update={"height_mm": height_mm}) for d in good()]


def _scaled(pdp: float | None = 200.0, embossed: bool = False):  # type: ignore[no-untyped-def]
    return ctx(pdp_area_cm2=pdp, mm_per_px=0.1, scale_source=ScaleSource.aruco, embossed=embossed)


def test_f1_tall_enough_pass() -> None:
    assert ids(run(_sized(2.5), _scaled(), only="F1")) == []


def test_f1_too_small_is_major() -> None:
    v = one(run(_sized(1.5), _scaled(), only="F1"), "F1")
    assert v.severity == Severity.major
    assert v.evidence.status == CheckStatus.fail


def test_f1_no_scale_is_unverifiable_info() -> None:
    v = one(run(good(), ctx(pdp_area_cm2=200.0), only="F1"), "F1")
    assert v.severity == Severity.info
    assert v.evidence.status == CheckStatus.unverifiable
    assert v.evidence.reason


def test_f1_scale_but_no_pdp_area_is_unverifiable() -> None:
    v = one(run(_sized(2.5), _scaled(pdp=None), only="F1"), "F1")
    assert v.evidence.status == CheckStatus.unverifiable


def test_f1_boundary_100cm2_needs_1mm() -> None:
    assert ids(run(_sized(1.0), _scaled(pdp=100.0), only="F1")) == []


def test_f1_embossed_doubles_threshold() -> None:
    assert ids(run(_sized(1.5), _scaled(pdp=100.0, embossed=True), only="F1")) == ["F1"]


# ---------------------------------------------------------------- F2 width ratio


def _ratio(r: float | None) -> list:  # type: ignore[type-arg]
    return [d.model_copy(update={"width_height_ratio": r}) for d in good()]


def test_f2_ratio_ok_pass() -> None:
    assert ids(run(_ratio(0.5), _scaled(), only="F2")) == []


def test_f2_too_narrow_is_minor() -> None:
    assert one(run(_ratio(0.2), _scaled(), only="F2"), "F2").severity == Severity.minor


def test_f2_not_measured_is_unverifiable() -> None:
    v = one(run(_ratio(None), ctx(), only="F2"), "F2")
    assert v.evidence.status == CheckStatus.unverifiable


def test_f2_exempt_characters_ignored() -> None:
    decls = [decl("net_quantity", "1", width_height_ratio=0.2)]
    assert ids(run(decls, _scaled(), only="F2")) == []


# ---------------------------------------------------------------- F3 medical device


def test_f3_medical_device_flags_and_skips_font_rules() -> None:
    v = run(
        _sized(0.5),
        _scaled().model_copy(update={"is_medical_device": True}),
        only={"F1", "F2", "F3"},
    )
    assert ids(v) == ["F3"]
    assert v[0].severity == Severity.info


def test_f3_not_medical_no_flag() -> None:
    assert ids(run(good(), only="F3")) == []


def test_f3_medical_without_scale_only_f3() -> None:
    v = run(good(), ctx(is_medical_device=True), only={"F1", "F3"})
    assert ids(v) == ["F3"]


# ---------------------------------------------------------------- P1 grouped on one panel


def test_p1_all_on_one_panel_pass() -> None:
    assert ids(run(good(), only="P1")) == []


def test_p1_split_across_panels_is_major() -> None:
    decls = replace(good(), "mrp", "MRP ₹20.00 (Inclusive of all taxes)", image_id="img2")
    v = one(run(decls, only="P1"), "P1")
    assert v.severity == Severity.major
    assert "mrp" in v.message


def test_p1_unknown_panel_is_unverifiable() -> None:
    decls = replace(good(), "mrp", "MRP ₹20.00 (Inclusive of all taxes)", image_id=None)
    assert one(run(decls, only="P1"), "P1").evidence.status == CheckStatus.unverifiable


# ---------------------------------------------------------------- P2 contrast


def _contrast(c: float | None) -> list:  # type: ignore[type-arg]
    return [d.model_copy(update={"contrast": c}) for d in good()]


def test_p2_good_contrast_pass() -> None:
    assert ids(run(_contrast(0.8), only="P2")) == []


def test_p2_low_contrast_is_major() -> None:
    assert one(run(_contrast(0.1), only="P2"), "P2").severity == Severity.major


def test_p2_not_measured_is_unverifiable() -> None:
    assert one(run(_contrast(None), only="P2"), "P2").evidence.status == CheckStatus.unverifiable


# ---------------------------------------------------------------- P3 bottom / crimp / seam


def test_p3_inspector_says_bottom_is_major() -> None:
    assert one(run(good(), ctx(on_bottom_or_seam=True), only="P3"), "P3").severity == Severity.major


def test_p3_inspector_says_fine_pass() -> None:
    assert ids(run(good(), ctx(on_bottom_or_seam=False), only="P3")) == []


def test_p3_not_asked_is_unverifiable() -> None:
    assert one(run(good(), ctx(), only="P3"), "P3").evidence.status == CheckStatus.unverifiable


# ---------------------------------------------------------------- P4 language


@pytest.mark.parametrize("langs", [["en"], ["hi"], ["en", "ta"]])
def test_p4_english_or_hindi_pass(langs: list[str]) -> None:
    assert ids(run(good(), ctx(languages=langs), only="P4")) == []


def test_p4_other_language_only_is_major() -> None:
    assert one(run(good(), ctx(languages=["ta"]), only="P4"), "P4").severity == Severity.major


def test_p4_unknown_language_is_unverifiable() -> None:
    assert (
        one(run(good(), ctx(languages=[]), only="P4"), "P4").evidence.status
        == CheckStatus.unverifiable
    )


# ---------------------------------------------------------------- E1 e-commerce listing


def test_e1_listing_without_date_pass() -> None:
    assert ids(run(without(good(), "mfg_date"), ctx(source=Source.ecommerce), only="E1")) == []


def test_e1_listing_missing_net_quantity_is_critical() -> None:
    v = one(run(without(good(), "net_quantity"), ctx(source=Source.ecommerce), only="E1"), "E1")
    assert v.severity == Severity.critical
    assert "net_quantity" in v.message
    assert v.rule_ref == "Rule 6(10)"


# ---------------------------------------------------------------- E2 origin filter


def test_e2_imported_listing_without_origin_is_info() -> None:
    v = one(run(good(), ctx(source=Source.ecommerce, is_imported=True), only="E2"), "E2")
    assert v.severity == Severity.info


def test_e2_imported_listing_with_origin_pass() -> None:
    decls = good() + [decl("country_of_origin", "Country of origin: Vietnam")]
    assert ids(run(decls, ctx(source=Source.ecommerce, is_imported=True), only="E2")) == []


# ---------------------------------------------------------------- X1 small pack


def test_x1_small_pack_downgrades_d1_to_info() -> None:
    v = run(without(good(), "manufacturer"), ctx(net_qty_g_or_ml=10.0), only={"D1", "X1"})
    assert ids(v) == ["D1", "X1"]
    assert one(v, "D1").severity == Severity.info


def test_x1_just_over_10g_not_exempt() -> None:
    v = run(without(good(), "manufacturer"), ctx(net_qty_g_or_ml=10.5), only={"D1", "X1"})
    assert ids(v) == ["D1"]
    assert v[0].severity == Severity.critical


def test_x1_unknown_quantity_not_exempt() -> None:
    v = run(without(good(), "manufacturer"), ctx(), only={"D1", "X1"})
    assert ids(v) == ["D1"]


def test_x1_mrp_still_required_on_small_pack() -> None:
    v = run(without(good(), "mrp"), ctx(net_qty_g_or_ml=5.0), only={"D5", "X1"})
    assert one(v, "D5").severity == Severity.critical


# ---------------------------------------------------------------- X2 restaurant food / X3 DPCO


@pytest.mark.parametrize(("flag", "code"), [("is_restaurant_food", "X2"), ("is_dpco_drug", "X3")])
def test_x2_x3_skip_declaration_rules(flag: str, code: str) -> None:
    v = run(without(good(), "manufacturer", "mrp"), ctx(**{flag: True}), only={"D1", "D5", code})
    assert ids(v) == [code]
    assert v[0].severity == Severity.info


@pytest.mark.parametrize("code", ["X2", "X3"])
def test_x2_x3_not_flagged_no_note(code: str) -> None:
    assert ids(run(good(), only=code)) == []


def test_x2_not_flagged_rules_still_apply() -> None:
    assert ids(run(without(good(), "manufacturer"), ctx(), only={"D1", "X2"})) == ["D1"]


# ---------------------------------------------------------------- X4 pan masala


def test_x4_pan_masala_note_only() -> None:
    v = run(without(good(), "manufacturer"), ctx(is_pan_masala=True), only={"D1", "X4"})
    assert ids(v) == ["D1", "X4"]
    assert one(v, "D1").severity == Severity.critical


def test_x4_not_flagged_no_note() -> None:
    assert ids(run(good(), only="X4")) == []


# ---------------------------------------------------------------- whole engine


def test_compliant_pack_has_no_scored_violations() -> None:
    v = run(good(), _scaled().model_copy(update={"on_bottom_or_seam": False}))
    assert [x.rule_id for x in v if x.evidence.status == CheckStatus.fail] == []


def test_bad_pack_lists_each_problem_once() -> None:
    decls = replace(good(), "mrp", "MRP Rs 20")
    decls = replace(decls, "net_quantity", "approx 500 g")
    decls = replace(decls, "consumer_care", "1800-123-4567")
    v = run(decls)
    failed = sorted(x.rule_id for x in v if x.evidence.status == CheckStatus.fail)
    assert failed == ["D3", "D5", "D6"]
