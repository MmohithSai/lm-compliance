"""`applies_to` filtering in run_rules. This part of the engine exists today, so no xfail."""

from __future__ import annotations

from pipeline.models import Source

from .helpers import ctx, good, ids, run, without


def test_d7_not_imported_not_applicable() -> None:
    assert ids(run(good(), only="D7")) == []


def test_e1_not_applied_to_packages() -> None:
    assert ids(run(without(good(), "net_quantity"), ctx(source=Source.package), only="E1")) == []


def test_e2_not_applied_to_packages() -> None:
    assert ids(run(good(), ctx(source=Source.package, is_imported=True), only="E2")) == []
