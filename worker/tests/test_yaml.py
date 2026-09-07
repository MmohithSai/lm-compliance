"""The YAML is the law. These pass today and keep the file honest as it is edited."""

from __future__ import annotations

import re

from pipeline.models import CheckStatus, Evidence, Severity, Violation
from pipeline.rules_engine import CHECKS, load_rules, score

RULES = load_rules()
CODE = re.compile(r"^[DFPEX]\d+[a-z]?$")


def test_yaml_has_rules() -> None:
    assert len(RULES) >= 20


def test_rule_ids_unique_and_well_formed() -> None:
    ids = [r.rule_id for r in RULES]
    assert len(ids) == len(set(ids))
    assert all(CODE.match(i) for i in ids), ids


def test_every_check_name_is_registered() -> None:
    missing = {r.check for r in RULES} - CHECKS.keys()
    assert not missing, f"unknown check functions in YAML: {missing}"


def test_field_present_rules_name_a_field() -> None:
    for r in RULES:
        if r.check == "field_present":
            assert r.params.get("field"), r.rule_id


def test_every_rule_has_ref_title_message() -> None:
    for r in RULES:
        assert r.rule_ref and r.title and r.message_template, r.rule_id


def test_exemptions_reference_x_rules() -> None:
    x_codes = {r.rule_id for r in RULES if r.rule_id.startswith("X")}
    for r in RULES:
        assert set(r.exemptions) <= x_codes, r.rule_id


def _v(sev: Severity, status: CheckStatus = CheckStatus.fail) -> Violation:
    return Violation(
        rule_id="T", rule_ref="t", severity=sev, message="m", evidence=Evidence(status=status)
    )


def test_score_penalties() -> None:
    assert score([]) == 100
    assert score([_v(Severity.critical), _v(Severity.major), _v(Severity.minor)]) == 62
    assert score([_v(Severity.info)]) == 100
    assert score([_v(Severity.critical)] * 5) == 0


def test_unverifiable_costs_nothing() -> None:
    assert score([_v(Severity.major, CheckStatus.unverifiable)]) == 100
