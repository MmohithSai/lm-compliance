"""Pipeline entry points. `run_local` is what the eval harness calls; `run_scan` wraps it."""

from __future__ import annotations

from pathlib import Path

from supabase import Client

from .models import PipelineResult, ScanContext, ScanRow


def run_local(images: list[Path], ctx: ScanContext) -> PipelineResult:
    """preprocess -> ocr -> extract -> measure -> rules -> score. No network."""
    raise NotImplementedError("P2")


def run_scan(sb: Client, scan: ScanRow) -> PipelineResult:
    """Download the scan's images, run_local, write words/declarations/violations/reports back."""
    raise NotImplementedError("P1")
