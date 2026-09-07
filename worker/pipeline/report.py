"""Report rendering (P5): Jinja2 HTML -> PDF (WeasyPrint), DOCX (python-docx), JSON."""

from __future__ import annotations

from pathlib import Path

from .models import PipelineResult, ScanRow

TEMPLATES = Path(__file__).resolve().parent / "templates"


def render_json(result: PipelineResult) -> str:
    return result.model_dump_json(indent=2)


def render_html(result: PipelineResult, scan: ScanRow) -> str:
    raise NotImplementedError("P5")


def render_pdf(html: str) -> bytes:
    raise NotImplementedError("P5")


def render_docx(result: PipelineResult, scan: ScanRow) -> bytes:
    raise NotImplementedError("P5")
