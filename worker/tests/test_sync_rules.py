"""P7. The rule catalogue the dashboard reads is a copy of the YAML, made by the worker.

The dashboard prints "D1 — Name and address of manufacturer / packer / importer". That title
exists in exactly one place, rules/pc_rules_2011.yaml, and this is the only thing that copies it
anywhere. If it ever stopped matching, the frontend would be quoting a law the engine is not
applying.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from supabase import Client

from main import sync_rules
from pipeline.rules_engine import load_rules


class FakeTable:
    def __init__(self, db: FakeClient, name: str) -> None:
        self.db, self.name = db, name

    def upsert(self, rows: list[dict[str, Any]]) -> FakeTable:
        self.db.upserted[self.name] = rows
        return self

    def execute(self) -> FakeTable:
        return self


class FakeClient:
    def __init__(self) -> None:
        self.upserted: dict[str, list[dict[str, Any]]] = {}

    def table(self, name: str) -> FakeTable:
        return FakeTable(self, name)


@pytest.fixture
def sb() -> FakeClient:
    return FakeClient()


def test_every_rule_in_the_yaml_is_written(sb: FakeClient) -> None:
    count = sync_rules(cast(Client, sb))
    rules = load_rules()
    assert count == len(rules)
    assert [r["rule_id"] for r in sb.upserted["rules"]] == [r.rule_id for r in rules]


def test_the_row_carries_what_the_dashboard_shows(sb: FakeClient) -> None:
    sync_rules(cast(Client, sb))
    by_id = {r["rule_id"]: r for r in sb.upserted["rules"]}
    d1 = by_id["D1"]
    assert d1["rule_ref"] == "Rule 6(1)(a)"
    assert d1["title"] == "Name and address of manufacturer / packer / importer"
    assert d1["severity"] == "critical"
    assert d1["synced_at"]


def test_the_titles_are_not_edited_on_the_way_through(sb: FakeClient) -> None:
    sync_rules(cast(Client, sb))
    written = {
        r["rule_id"]: (r["rule_ref"], r["title"], r["severity"]) for r in sb.upserted["rules"]
    }
    for rule in load_rules():
        assert written[rule.rule_id] == (rule.rule_ref, rule.title, rule.severity.value)
