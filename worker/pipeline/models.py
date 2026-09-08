"""Typed contracts shared across the pipeline. No bare dicts cross module boundaries."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(StrEnum):
    critical = "critical"
    major = "major"
    minor = "minor"
    info = "info"


class Source(StrEnum):
    package = "package"
    ecommerce = "ecommerce"


class ScaleSource(StrEnum):
    aruco = "aruco"
    card = "card"
    inspector = "inspector"
    none = "none"


class CheckStatus(StrEnum):
    fail = "fail"
    unverifiable = "unverifiable"


class Word(BaseModel):
    """One OCR box. Pixel coords in the preprocessed image."""

    id: int
    image_id: str
    text: str
    x: int
    y: int
    w: int
    h: int
    confidence: float


class Declaration(BaseModel):
    field: str  # canonical name, see CLAUDE.md
    value: str
    confidence: float = 1.0
    word_ids: list[int] = Field(default_factory=list)
    image_id: str | None = None
    height_mm: float | None = None  # None = no scale, not verifiable
    width_height_ratio: float | None = None
    contrast: float | None = None  # 0..1, None = not measured
    extractor: str = "regex_layout"


class ScanContext(BaseModel):
    """What the rule engine may know besides the declarations. Unknown = None, never guessed."""

    source: Source = Source.package
    is_imported: bool = False
    pdp_area_cm2: float | None = None
    # The inspector's own tape measure, and the last resort for a scale: with no marker and no
    # card in the frame, the panel's width in millimetres against the photo's width in pixels.
    pdp_width_mm: float | None = None
    has_reference_card: bool = False  # only then is a card-shaped rectangle a card
    mm_per_px: float | None = None
    scale_source: ScaleSource = ScaleSource.none
    embossed: bool = False
    is_medical_device: bool = False
    net_qty_g_or_ml: float | None = None
    is_restaurant_food: bool = False
    is_dpco_drug: bool = False
    is_pan_masala: bool = False
    on_bottom_or_seam: bool | None = None  # inspector's answer; None = not asked
    languages: list[str] = Field(default_factory=lambda: ["en"])
    today: date = Field(default_factory=date.today)


class Evidence(BaseModel):
    word_ids: list[int] = Field(default_factory=list)
    values: dict[str, str] = Field(default_factory=dict)
    status: CheckStatus = CheckStatus.fail
    reason: str | None = None


class Violation(BaseModel):
    rule_id: str
    rule_ref: str
    severity: Severity
    message: str
    evidence: Evidence = Field(default_factory=Evidence)
    confidence: float = 1.0


class Rule(BaseModel):
    """One entry of rules/pc_rules_2011.yaml."""

    rule_id: str
    rule_ref: str
    title: str
    severity: Severity
    check: str
    message_template: str
    applies_to: Literal["all", "imported", "ecommerce"] = "all"
    exemptions: list[str] = Field(default_factory=list)
    params: dict[str, str] = Field(default_factory=dict)
    verify: bool = False  # rule_ref still to be cross-checked against docs/law/


class PipelineResult(BaseModel):
    words: list[Word]
    declarations: list[Declaration]
    violations: list[Violation]
    mm_per_px: float | None
    scale_source: ScaleSource
    compliance_score: int


class ScanRow(BaseModel):
    """The subset of the scans table the worker needs."""

    id: str
    inspector_id: str
    source: Source = Source.package
    has_reference_card: bool = False
    pdp_width_mm: float | None = None
    pdp_height_mm: float | None = None
