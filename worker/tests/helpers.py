"""Small builders shared by the tests. Plain functions, no fixtures."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from pipeline.models import Declaration, ScanContext, Violation
from pipeline.rules_engine import load_rules, run_rules

TODAY = date(2026, 9, 6)
RULES = load_rules()


def decl(field: str, value: str, **kw: Any) -> Declaration:
    kw.setdefault("image_id", "img1")
    return Declaration(field=field, value=value, **kw)


def good() -> list[Declaration]:
    """A fully compliant domestic pack, all on one panel."""
    return [
        decl("manufacturer", "Parle Products Pvt Ltd, Vile Parle (East), Mumbai 400057"),
        decl("generic_name", "Biscuits"),
        decl("net_quantity", "Net Qty: 200 g"),
        decl("mfg_date", "Mfd: 03/2026"),
        decl("mrp", "MRP ₹20.00 (Inclusive of all taxes)"),
        decl("consumer_care", "Consumer care: Parle, Mumbai; 1800-123-4567; care@parle.com"),
        decl("unit_sale_price", "₹10.00 per 100 g"),
        decl("best_before", "Best before 6 months from packaging"),
    ]


def without(decls: list[Declaration], *fields: str) -> list[Declaration]:
    return [d for d in decls if d.field not in fields]


def replace(decls: list[Declaration], field: str, value: str, **kw: Any) -> list[Declaration]:
    return without(decls, field) + [decl(field, value, **kw)]


def ctx(**kw: Any) -> ScanContext:
    kw.setdefault("today", TODAY)
    return ScanContext(**kw)


def run(
    decls: list[Declaration],
    context: ScanContext | None = None,
    only: str | Iterable[str] | None = None,
) -> list[Violation]:
    """Run the engine on a subset of rules (by rule_id) so each test isolates one behaviour."""
    wanted = {only} if isinstance(only, str) else (set(only) if only is not None else None)
    rules = [r for r in RULES if wanted is None or r.rule_id in wanted]
    return run_rules(decls, context or ctx(), rules)


def ids(violations: list[Violation]) -> list[str]:
    return sorted(v.rule_id for v in violations)


def one(violations: list[Violation], rule_id: str) -> Violation:
    found = [v for v in violations if v.rule_id == rule_id]
    assert len(found) == 1, f"expected exactly one {rule_id}, got {ids(violations)}"
    return found[0]
