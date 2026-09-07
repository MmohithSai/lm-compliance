"""Deterministic rule engine. Reads rules/pc_rules_2011.yaml. No AI here, ever."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import yaml

from .models import CheckStatus, Declaration, Rule, ScanContext, Severity, Source, Violation

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


def _not_built(decls: list[Declaration], ctx: ScanContext, rule: Rule) -> list[Violation]:
    raise NotImplementedError(f"P3: check '{rule.check}' not built yet")


# Every `check:` name the YAML may use. P3 replaces _not_built one by one; tests/test_rules.py
# already pins the behaviour of each.
CHECK_NAMES = [
    "field_present",
    "net_quantity_valid",
    "date_valid_not_future",
    "mrp_valid",
    "single_mrp",
    "consumer_care_valid",
    "origin_required_if_imported",
    "font_height_table1",
    "font_width_ratio",
    "medical_device_flag",
    "grouped_on_one_panel",
    "contrast_ok",
    "not_on_bottom_or_seam",
    "language_ok",
    "ecommerce_all_declarations",
    "ecommerce_origin_filter",
    "exemption_small_pack",
    "exemption_restaurant_food",
    "exemption_dpco_drug",
    "exemption_pan_masala",
]
CHECKS: dict[str, Check] = dict.fromkeys(CHECK_NAMES, _not_built)


def run_rules(
    decls: list[Declaration], ctx: ScanContext, rules: list[Rule] | None = None
) -> list[Violation]:
    """Apply every applicable rule. Exemption downgrades (X1..X4) are applied in P3."""
    rules = rules if rules is not None else load_rules()
    if any(d.field == "importer" for d in decls):
        ctx = ctx.model_copy(update={"is_imported": True})
    out: list[Violation] = []
    for rule in rules:
        if rule.applies_to == "imported" and not ctx.is_imported:
            continue
        if rule.applies_to == "ecommerce" and ctx.source != Source.ecommerce:
            continue
        out.extend(CHECKS[rule.check](decls, ctx, rule))
    return out


def score(violations: list[Violation]) -> int:
    """100 minus penalties. Unverifiable checks and info rows never cost points."""
    counted = (v for v in violations if v.evidence.status == CheckStatus.fail)
    return max(0, 100 - sum(PENALTY[v.severity] for v in counted))
