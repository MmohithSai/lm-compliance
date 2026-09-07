"""Extractor interface. Deterministic today; a local-model extractor may implement it later."""

from __future__ import annotations

from typing import Protocol

from ..models import Declaration, ScanContext, Word


class Extractor(Protocol):
    name: str

    def extract(self, words: list[Word], ctx: ScanContext) -> list[Declaration]: ...
