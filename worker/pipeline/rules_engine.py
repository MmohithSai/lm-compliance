"""Deterministic rule engine. Reads rules/pc_rules_2011.yaml. No AI here, ever."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from .measure import MIN_RATIO, RATIO_EXEMPT_CHARS, min_height_mm
from .models import (
    CheckStatus,
    Declaration,
    Evidence,
    Rule,
    ScanContext,
    Severity,
    Source,
    Violation,
)

RULES_PATH = Path(__file__).resolve().parents[2] / "rules" / "pc_rules_2011.yaml"
Check = Callable[[list[Declaration], ScanContext, Rule], list[Violation]]

PENALTY: dict[Severity, int] = {
    Severity.critical: 25,
    Severity.major: 10,
    Severity.minor: 3,
    Severity.info: 0,
}


def load_rules(path: Path = RULES_PATH) -> list[Rule]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Rule.model_validate(r) for r in data["rules"]]


# ---------------------------------------------------------------- reading a declaration


def _decl(decls: list[Declaration], field: str) -> Declaration | None:
    """First declaration of this field in reading order. Blank counts as absent."""
    return next((d for d in decls if d.field == field and d.value.strip()), None)


def _fail(rule: Rule, evidence: Evidence, **kw: object) -> list[Violation]:
    return [
        Violation(
            rule_id=rule.rule_id,
            rule_ref=rule.rule_ref,
            severity=rule.severity,
            message=rule.message_template.format(**kw),
            evidence=evidence,
        )
    ]


def _unverifiable(rule: Rule, reason: str) -> list[Violation]:
    """Never invent a measurement. An unverifiable check is reported and costs no points."""
    return [
        Violation(
            rule_id=rule.rule_id,
            rule_ref=rule.rule_ref,
            severity=Severity.info,
            message=f"{rule.title}: not verifiable. {reason}",
            evidence=Evidence(status=CheckStatus.unverifiable, reason=reason),
        )
    ]


# ---------------------------------------------------------------- text tests
# Each pattern below was checked against the values in eval/dataset/*/gold.json, which are
# transcribed off real Indian packs. Nothing here is invented from the wording of the law alone.

# An address, not just a name. Indian labels print a six digit PIN; where the print (or the OCR)
# loses it, an address is still several comma separated parts, which a company name never is.
PIN = re.compile(r"\b\d{6}\b")

# Standard units of Rule 8: SI symbols plus the count. Spelled out forms ("500 gms", "1 dozen")
# are not standard units and the law means the symbol.
UNIT = r"(?:mg|kg|ml|cl|dl|kl|km|mm|cm|pcs|pc|g|l|m|n|u)"
QUANTITY = re.compile(rf"\d+(?:[.,]\d+)?\s*{UNIT}(?![a-z])", re.IGNORECASE)
QUALIFIER = re.compile(r"\b(approx|approximately|about|around|nearly)\b", re.IGNORECASE)

# g / ml for the Rule 26(a) ten gram exemption. A count ("12 pcs") has no weight.
IN_GRAMS = {"mg": 0.001, "g": 1.0, "kg": 1000.0, "ml": 1.0, "cl": 10.0, "dl": 100.0, "l": 1000.0}
NET_QTY = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|kg|ml|cl|dl|g|l)(?![a-z])", re.IGNORECASE)

MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
MONTH_NAME = "|".join(MONTHS)
# Tried in this order; the first one that yields a real month and year wins. Indian packs print
# the day first ("PKD. 24/01/25"), so the middle number of a three part date is the month.
DATE_FORMS: list[tuple[re.Pattern[str], tuple[int, int]]] = [
    (re.compile(r"\d{1,2}[./-](\d{1,2})[./-](\d{2,4})"), (1, 2)),  # DD/MM/YY(YY)
    (re.compile(r"(?<!\d)(\d{4})[./-](\d{1,2})(?!\d)"), (2, 1)),  # YYYY-MM
    (re.compile(r"(?<!\d)(\d{1,2})[./-](\d{4})(?!\d)"), (1, 2)),  # MM/YYYY
    (re.compile(r"(?<!\d)(\d{1,2})[./-](\d{2})(?![\d./-])"), (1, 2)),  # MM/YY
    (re.compile(rf"({MONTH_NAME})[a-z]*[\s./-]*(\d{{2,4}})", re.IGNORECASE), (1, 2)),  # JUL/25
]

AMOUNT = re.compile(r"\d+(?:,\d{2,3})*(?:\.\d{1,2})?")
# No PP-OCR dictionary contains a rupee sign, but "Rs" and "INR" survive OCR and Rule 2(m)
# accepts either. See the Decisions log for what this costs on a photographed pack.
CURRENCY = re.compile(r"₹|\brs\b\.?|\binr\b", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A phone number is eight or more digits in one run of digits and separators. Eight, so a PIN
# code in the same address block is not mistaken for one.
PHONE_RUN = re.compile(r"\d[\d\s().+-]{6,}\d")

OK_LANGUAGES = {"en", "hi"}

# Rule 9(1)(a) groups the declarations of Rule 6(1). unit_sale_price and best_before are not
# among them, so they do not put a pack in breach of P1.
MANDATORY = (
    "manufacturer",
    "importer",
    "generic_name",
    "net_quantity",
    "mfg_date",
    "mrp",
    "consumer_care",
    "country_of_origin",
)
# Rule 6(10): everything under Rule 6(1) except the month and year.
LISTING_REQUIRED = ("generic_name", "net_quantity", "mrp", "consumer_care")


def _squash(s: str) -> str:
    """Letters and digits only. 'M.R.P.' and 'MRP', 'Incl. of' and 'inclusive of' line up."""
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def _has_address(value: str) -> bool:
    return bool(PIN.search(value)) or (value.count(",") >= 2 and len(value) >= 25)


def net_qty_g_or_ml(value: str) -> float | None:
    """The declared quantity in g / ml, or None if it is a count or unreadable."""
    m = NET_QTY.search(value)
    return round(float(m.group(1)) * IN_GRAMS[m.group(2).lower()], 3) if m else None


def month_and_year(value: str) -> tuple[int, int] | None:
    """(year, month) of the first readable date in the line, or None."""
    for pattern, (month_group, year_group) in DATE_FORMS:
        for m in pattern.finditer(value):
            raw_month = m.group(month_group)
            month = MONTHS.index(raw_month[:3].lower()) + 1 if raw_month[0].isalpha() else 0
            month = month or int(raw_month)
            year = int(m.group(year_group))
            if 1 <= month <= 12:
                return (year if year > 100 else 2000 + year), month
    return None


def _price(value: str) -> float | None:
    m = AMOUNT.search(value)
    return float(m.group().replace(",", "")) if m else None


# ---------------------------------------------------------------- the checks
# One function per `check:` name in the YAML. Each returns the violations for that rule alone;
# run_rules decides which rules are applicable and which exemptions apply.


def _field_present(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """D1, D2, D8, D9: the named field (or its alternative) is there, with an address if asked."""
    needs_address = rule.params.get("needs_address") == "true"
    fields = [rule.params["field"], *filter(None, [rule.params.get("alt")])]
    found = [d for d in (_decl(decls, f) for f in fields) if d is not None]
    if any(not needs_address or _has_address(d.value) for d in found):
        return []
    values = {d.field: d.value for d in found}
    word_ids = [i for d in found for i in d.word_ids]
    return _fail(rule, Evidence(word_ids=word_ids, values=values))


def _net_quantity_valid(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """D3: a number in a standard unit, with no 'approx' softening it."""
    found = _decl(decls, "net_quantity")
    value = found.value if found else ""
    if found and QUANTITY.search(value) and not QUALIFIER.search(value):
        return []
    evidence = Evidence(word_ids=found.word_ids if found else [], values={"net_quantity": value})
    return _fail(rule, evidence, value=value)


def _date_valid_not_future(
    decls: list[Declaration], ctx: ScanContext, rule: Rule
) -> list[Violation]:
    """D4: a month and a year that has already happened."""
    found = _decl(decls, "mfg_date")
    value = found.value if found else ""
    parsed = month_and_year(value) if found else None
    if parsed is not None and parsed <= (ctx.today.year, ctx.today.month):
        return []
    evidence = Evidence(word_ids=found.word_ids if found else [], values={"mfg_date": value})
    return _fail(rule, evidence, value=value)


def _mrp_valid(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """D5: 'MRP' or 'Maximum Retail Price', an amount, and 'inclusive of all taxes'.

    Rule 2(m) also wants the amount marked as rupees, and that one part is not checkable from a
    photograph: no PP-OCR dictionary contains ₹ (all 56 checked, see the Decisions log), so the
    extractor never sees one. Demanding the glyph measured the dictionary, not the pack — it
    failed eleven eval cases whose price line was read word for word right. So the marker is
    reported as unverifiable and the other three parts of the rule are still enforced.
    """
    found = _decl(decls, "mrp")
    value = found.value if found else ""
    squashed = _squash(value)
    named = "mrp" in squashed or "maximumretailprice" in squashed
    taxed = re.search(r"incl(usive)?ofalltaxes", squashed) is not None
    if not (found and named and taxed and _price(value) is not None):
        evidence = Evidence(word_ids=found.word_ids if found else [], values={"mrp": value})
        return _fail(rule, evidence, value=value)
    if CURRENCY.search(value) is None:
        return _unverifiable(
            rule,
            f"'{value}' reads as a retail sale price, but no OCR model can print a rupee sign. "
            "Check by eye that the amount is marked ₹ or Rs.",
        )
    return []


def _single_mrp(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """D5b: one retail sale price on the pack. A repriced sticker over the print is two."""
    prices = {p: d for d in decls if d.field == "mrp" and (p := _price(d.value)) is not None}
    if len(prices) < 2:
        return []
    found = ", ".join(f"{p:.2f}" for p in sorted(prices))
    word_ids = [i for d in prices.values() for i in d.word_ids]
    return _fail(rule, Evidence(word_ids=word_ids, values={"mrp": found}), found=found)


def _consumer_care_valid(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """D6: a telephone number and an e-mail address the consumer can actually use."""
    found = _decl(decls, "consumer_care")
    value = found.value if found else ""
    has_email = EMAIL.search(value) is not None
    digits = (re.sub(r"\D", "", m.group()) for m in PHONE_RUN.finditer(EMAIL.sub(" ", value)))
    if found and has_email and any(len(d) >= 8 for d in digits):
        return []
    evidence = Evidence(word_ids=found.word_ids if found else [], values={"consumer_care": value})
    return _fail(rule, evidence, value=value)


def _origin_required_if_imported(
    decls: list[Declaration], ctx: ScanContext, rule: Rule
) -> list[Violation]:
    """D7: run_rules has already decided the pack is imported."""
    found = _decl(decls, "country_of_origin")
    return [] if found else _fail(rule, Evidence())


def _font_height_table1(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """F1: every declaration at least as tall as Table I asks for this panel area."""
    if ctx.is_medical_device:
        return []  # F3 says which rules apply instead
    measured = [(h, d) for d in decls if (h := d.height_mm) is not None]
    if ctx.mm_per_px is None or not measured:
        return _unverifiable(
            rule,
            "No scale: photograph the panel with an ArUco marker or a card in frame, or enter "
            "the panel size on the upload form.",
        )
    if ctx.pdp_area_cm2 is None:
        return _unverifiable(
            rule, "The principal display panel area is unknown, so Table I has no row to apply."
        )
    need = min_height_mm(ctx.pdp_area_cm2, ctx.embossed)
    short = sorted(((h, d) for h, d in measured if h < need), key=lambda p: (p[0], p[1].field))
    if not short:
        return []
    height, worst = short[0]
    return _fail(
        rule,
        Evidence(word_ids=worst.word_ids, values={d.field: f"{h} mm" for h, d in short}),
        field=worst.field,
        height_mm=height,
        min_mm=need,
        pdp_area_cm2=ctx.pdp_area_cm2,
    )


def _font_width_ratio(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """F2: characters at least a third as wide as they are tall."""
    if ctx.is_medical_device:
        return []
    eligible = [d for d in decls if set(re.sub(r"\W", "", d.value)) - RATIO_EXEMPT_CHARS]
    if not eligible:
        return []  # nothing but 1, i, I and l on the panel: Rule 7 exempts them
    measured = [(r, d) for d in eligible if (r := d.width_height_ratio) is not None]
    if not measured:
        return _unverifiable(
            rule, "Character width was not measured: the photo has no scale reference."
        )
    thin = ((r, d) for r, d in measured if r < MIN_RATIO)
    narrow = sorted(thin, key=lambda p: (p[0], p[1].field))
    if not narrow:
        return []
    ratio, worst = narrow[0]
    return _fail(
        rule,
        Evidence(word_ids=worst.word_ids, values={d.field: f"{r}" for r, d in narrow}),
        field=worst.field,
        ratio=ratio,
    )


def _medical_device_flag(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """F3: a note that the Medical Devices Rules replace Table I. F1 and F2 stand down."""
    return _fail(rule, Evidence()) if ctx.is_medical_device else []


def _grouped_on_one_panel(
    decls: list[Declaration], ctx: ScanContext, rule: Rule
) -> list[Violation]:
    """P1: the Rule 6(1) declarations are together, not scattered over the pack.

    One photograph showing them all is proof they are grouped. Two photographs are not proof of
    the opposite: nothing here places one photo relative to another, and two shots of one back
    panel look exactly like two panels. Measured on 2026-09-08: as a failure this accused five
    eval cases whose extra frames were overlapping crops of the same panel
    (eval/results/2026-09-08_p3-rules.json). P4's scale reference is what will tell panels apart.
    """
    relevant = [d for d in decls if d.field in MANDATORY]
    if any(d.image_id is None for d in relevant):
        return _unverifiable(rule, "At least one declaration was not tied to a photographed panel.")
    panels = {d.image_id for d in relevant}
    if len(panels) < 2:
        return []
    found = ", ".join(f"{d.field} on {d.image_id}" for d in sorted(relevant, key=lambda d: d.field))
    return _unverifiable(
        rule,
        f"The declarations were read from {len(panels)} photographs ({found}), and two "
        "photographs may show the same panel twice. Shoot the whole panel in one frame.",
    )


def _contrast_ok(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """P2: printed in contrast with the background."""
    floor = float(rule.params.get("min_contrast", "0.5"))
    measured = [(c, d) for d in decls if (c := d.contrast) is not None]
    if not measured:
        return _unverifiable(
            rule,
            "No scale: contrast is only judged on a photo shot to be measured, with an ArUco "
            "marker or a card in the frame. Without one this number is the lighting and the "
            "focus, not the print.",
        )
    faint = sorted(((c, d) for c, d in measured if c < floor), key=lambda p: (p[0], p[1].field))
    if not faint:
        return []
    contrast, worst = faint[0]
    return _fail(
        rule,
        Evidence(word_ids=worst.word_ids, values={d.field: f"{c}" for c, d in faint}),
        field=worst.field,
        contrast=contrast,
    )


def _not_on_bottom_or_seam(
    decls: list[Declaration], ctx: ScanContext, rule: Rule
) -> list[Violation]:
    """P3: the inspector's answer. Nothing in the photo can settle this."""
    if ctx.on_bottom_or_seam is None:
        return _unverifiable(
            rule, "The inspector was not asked whether the declarations sit on a bottom or seam."
        )
    return _fail(rule, Evidence()) if ctx.on_bottom_or_seam else []


def _language_ok(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """P4: English or Hindi, whatever else is on the pack alongside."""
    found = ", ".join(ctx.languages)
    if not ctx.languages:
        return _unverifiable(rule, "No language was detected on the panel.")
    if set(ctx.languages) & OK_LANGUAGES:
        return []
    return _fail(rule, Evidence(values={"languages": found}), found=found)


def _ecommerce_all_declarations(
    decls: list[Declaration], ctx: ScanContext, rule: Rule
) -> list[Violation]:
    """E1: Rule 6(10) wants everything of Rule 6(1) on the listing except the month and year."""
    present = {d.field for d in decls if d.value.strip()}
    missing = [] if present & {"manufacturer", "importer"} else ["manufacturer"]
    missing += [f for f in LISTING_REQUIRED if f not in present]
    if ctx.is_imported and "country_of_origin" not in present:
        missing.append("country_of_origin")
    if not missing:
        return []
    found = ", ".join(missing)
    return _fail(rule, Evidence(values={"missing": found}), missing=found)


def _ecommerce_origin_filter(
    decls: list[Declaration], ctx: ScanContext, rule: Rule
) -> list[Violation]:
    """E2: the platform's country of origin filter. A note, not a scored violation."""
    if not ctx.is_imported or _decl(decls, "country_of_origin"):
        return []
    return _fail(rule, Evidence())


# Rule 26. X1 leaves the rules in force but unenforced (reported as info); X2 and X3 take the
# package out of the Rules entirely; X4 is a note to the inspector and changes nothing.
EXEMPT_WHEN: dict[str, Callable[[ScanContext], bool]] = {
    "X1": lambda c: c.net_qty_g_or_ml is not None and c.net_qty_g_or_ml <= 10.0,
    "X2": lambda c: c.is_restaurant_food,
    "X3": lambda c: c.is_dpco_drug,
    "X4": lambda c: c.is_pan_masala,
}
SKIPS_THE_RULE = {"X2", "X3"}


def _exemption(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    """X1..X4: the note that says why a rule was downgraded, skipped or flagged."""
    if not EXEMPT_WHEN[rule.rule_id](ctx):
        return []
    qty = ctx.net_qty_g_or_ml
    return _fail(
        rule,
        Evidence(values={"exemption": rule.rule_ref}),
        net_qty=f"{qty:g} g/ml" if qty is not None else "unknown",
    )


CHECKS: dict[str, Check] = {
    "field_present": _field_present,
    "net_quantity_valid": _net_quantity_valid,
    "date_valid_not_future": _date_valid_not_future,
    "mrp_valid": _mrp_valid,
    "single_mrp": _single_mrp,
    "consumer_care_valid": _consumer_care_valid,
    "origin_required_if_imported": _origin_required_if_imported,
    "font_height_table1": _font_height_table1,
    "font_width_ratio": _font_width_ratio,
    "medical_device_flag": _medical_device_flag,
    "grouped_on_one_panel": _grouped_on_one_panel,
    "contrast_ok": _contrast_ok,
    "not_on_bottom_or_seam": _not_on_bottom_or_seam,
    "language_ok": _language_ok,
    "ecommerce_all_declarations": _ecommerce_all_declarations,
    "ecommerce_origin_filter": _ecommerce_origin_filter,
    "exemption_small_pack": _exemption,
    "exemption_restaurant_food": _exemption,
    "exemption_dpco_drug": _exemption,
    "exemption_pan_masala": _exemption,
}


def _applies(rule: Rule, ctx: ScanContext) -> bool:
    """A screenshot is not the package. On an e-commerce scan only Rule 6(10) can be judged:
    what is printed on the pack is not in the frame, so the package rules have no evidence."""
    if rule.applies_to == "ecommerce":
        return ctx.source == Source.ecommerce
    if ctx.source == Source.ecommerce:
        return False
    return rule.applies_to != "imported" or ctx.is_imported


def _with_what_the_declarations_say(decls: list[Declaration], ctx: ScanContext) -> ScanContext:
    """Two context fields the pack itself answers. The inspector's answer always wins."""
    updates: dict[str, Any] = {}
    if any(d.field == "importer" for d in decls):
        updates["is_imported"] = True
    qty = _decl(decls, "net_quantity")
    if ctx.net_qty_g_or_ml is None and qty is not None:
        grams = net_qty_g_or_ml(qty.value)
        if grams is not None:
            updates["net_qty_g_or_ml"] = grams
    return ctx.model_copy(update=updates) if updates else ctx


def applicable_rules(
    decls: list[Declaration], ctx: ScanContext, rules: list[Rule] | None = None
) -> list[Rule]:
    """The rules this scan was actually judged against, in order.

    The report needs this to say which checks *passed*: `run_rules` only returns what went
    wrong, and a rule that raised nothing is indistinguishable from a rule Rule 26 or Rule 6(10)
    never applied. Deriving that twice — once here, once in the report — is how the law drifts.
    """
    rules = rules if rules is not None else load_rules()
    ctx = _with_what_the_declarations_say(decls, ctx)
    return [
        rule
        for rule in rules
        if _applies(rule, ctx)
        and not ({x for x in rule.exemptions if EXEMPT_WHEN[x](ctx)} & SKIPS_THE_RULE)
    ]


def run_rules(
    decls: list[Declaration], ctx: ScanContext, rules: list[Rule] | None = None
) -> list[Violation]:
    """Apply every applicable rule, with the Rule 26 exemptions."""
    rules = rules if rules is not None else load_rules()
    ctx = _with_what_the_declarations_say(decls, ctx)
    out: list[Violation] = []
    for rule in applicable_rules(decls, ctx, rules):
        active = {x for x in rule.exemptions if EXEMPT_WHEN[x](ctx)}
        found = CHECKS[rule.check](decls, ctx, rule)
        if active:  # X1: still reported, so the inspector sees it, but it costs no points
            found = [v.model_copy(update={"severity": Severity.info}) for v in found]
        out.extend(found)
    return out


def score(violations: list[Violation]) -> int:
    """100 minus penalties. Unverifiable checks and info rows never cost points."""
    counted = (v for v in violations if v.evidence.status == CheckStatus.fail)
    return max(0, 100 - sum(PENALTY[v.severity] for v in counted))
