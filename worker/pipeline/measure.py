"""Scale and font geometry (P4). Never invents a measurement: None means "not verifiable"."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .models import ScaleSource

ARUCO_DICT_NAME = "DICT_4X4_50"
ARUCO_MARKER_MM = 50.0  # printed reference card: one 50 mm marker
CARD_MM = (85.6, 54.0)  # ISO/IEC 7810 ID-1 (credit card)
RATIO_EXEMPT_CHARS = set("1iIl")  # Rule 7: width >= 1/3 height except these


def mm_per_px_from_aruco(
    img: NDArray[np.uint8], marker_mm: float = ARUCO_MARKER_MM
) -> float | None:
    raise NotImplementedError("P4")


def mm_per_px_from_card(img: NDArray[np.uint8]) -> float | None:
    raise NotImplementedError("P4")


def resolve_scale(
    img: NDArray[np.uint8], pdp_width_mm: float | None, pdp_px_width: int | None
) -> tuple[float | None, ScaleSource]:
    """Priority: ArUco -> card -> inspector PDP mm -> (None, ScaleSource.none)."""
    raise NotImplementedError("P4")


def pdp_area_cm2(width_mm: float, height_mm: float) -> float:
    """Rule 8, rectangular packages only (cylinders are out of scope for the MVP)."""
    raise NotImplementedError("P4")


def min_height_mm(pdp_area_cm2: float, embossed: bool = False) -> float:
    """Rule 7 Table-I."""
    raise NotImplementedError("P4")


def text_height_mm(word_h_px: int, mm_per_px: float) -> float:
    raise NotImplementedError("P4")


def width_ratio_ok(char_width_mm: float, height_mm: float, text: str) -> bool:
    """Rule 7: numeral/letter width >= 1/3 of height, except 1, i, I, l."""
    raise NotImplementedError("P4")
