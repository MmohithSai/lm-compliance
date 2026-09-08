"""Every eval/dataset/<case>/gold.json is well formed.

Gold files are hand written for 40-60 real photos. A typo in a field name or a rule code is
invisible in the eval output: it just scores as a permanent miss. This test catches it instead.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from pipeline.extractors.regex_layout import ANCHORS
from pipeline.models import Declaration, ScanContext, Severity
from pipeline.rules_engine import load_rules, run_rules

DATASET = Path(__file__).resolve().parents[2] / "eval" / "dataset"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
FIELDS = set(ANCHORS)  # the canonical declaration names, single source of truth
RULES = {r.rule_id: r for r in load_rules()}
# the eval compares non-info predictions only, so an info code in gold could never be matched
SCORING_CODES = {i for i, r in RULES.items() if r.severity != Severity.info}

# Gold is a fixed transcript of a photograph, so the verdict has to be reproducible: pin
# "today" instead of letting the calendar decide whether a date is in the future.
TODAY = date(2026, 9, 8)

CASES = sorted(p.name for p in DATASET.iterdir() if (p / "gold.json").exists())


def gold(case: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((DATASET / case / "gold.json").read_text(encoding="utf-8"))
    return data


def test_dataset_is_not_empty() -> None:
    assert CASES, f"no cases with a gold.json under {DATASET}"


@pytest.mark.parametrize("case", CASES)
def test_case_has_an_image(case: str) -> None:
    images = [p for p in (DATASET / case).iterdir() if p.suffix.lower() in IMAGE_EXT]
    assert images, f"{case}: gold.json but no image"


@pytest.mark.parametrize("case", CASES)
def test_context_keys_are_scan_context_fields(case: str) -> None:
    unknown = set(gold(case).get("context", {})) - set(ScanContext.model_fields)
    assert not unknown, f"{case}: unknown context keys {unknown}"
    ScanContext.model_validate(gold(case).get("context", {}))


@pytest.mark.parametrize("case", CASES)
def test_declaration_fields_are_canonical(case: str) -> None:
    decls: dict[str, str] = gold(case).get("declarations", {})
    assert set(decls) <= FIELDS, f"{case}: unknown fields {set(decls) - FIELDS}"
    assert all(v.strip() for v in decls.values()), f"{case}: an empty declaration value"


@pytest.mark.parametrize("case", CASES)
def test_violation_codes_exist_and_score(case: str) -> None:
    codes = gold(case)["violations"]
    assert len(codes) == len(set(codes)), f"{case}: duplicate codes in violations"
    unknown = set(codes) - set(RULES)
    assert not unknown, f"{case}: rule codes not in the YAML: {unknown}"
    info_only = set(codes) - SCORING_CODES
    assert not info_only, f"{case}: info-severity codes can never be matched: {info_only}"


# Read off the pixels, not off the text: gold declarations cannot produce them.
MEASURED_CODES = {"F1", "F2", "P2"}


@pytest.mark.parametrize("case", CASES)
def test_engine_reproduces_gold_from_gold_declarations(case: str) -> None:
    """The rule engine, fed the declarations a human read off the photo, gets gold's verdict.

    The eval measures extraction *and* rules together, so a rule bug hides behind an OCR miss.
    This separates them: 37 hand written cases, no OCR. A failure here is either the engine or
    the gold file, and both are worth knowing about.

    F1, F2 and P2 are left out of the comparison. Gold holds the declarations as printed, and
    those three read a measurement off the pixels — `height_mm`, the width/height ratio and the
    contrast — which no amount of text can stand in for. Fed text alone the engine correctly
    reports them "not verifiable", so demanding them here would only pin that it does.
    """
    data = gold(case)
    decls = [Declaration(field=f, value=v) for f, v in data["declarations"].items()]
    context = ScanContext.model_validate({"today": TODAY, **data.get("context", {})})
    predicted = {v.rule_id for v in run_rules(decls, context) if v.severity != Severity.info}
    assert predicted == set(data["violations"]) - MEASURED_CODES
