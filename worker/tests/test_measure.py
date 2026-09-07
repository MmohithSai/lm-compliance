"""Scale detection and Rule 7 geometry. Written before measure.py is built (P4).

Delete the xfail line when the functions land; strict mode fails the suite if it is left behind.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from numpy.typing import NDArray

from pipeline.measure import (
    ARUCO_MARKER_MM,
    min_height_mm,
    mm_per_px_from_aruco,
    pdp_area_cm2,
    resolve_scale,
    text_height_mm,
    width_ratio_ok,
)
from pipeline.models import ScaleSource

pytestmark = pytest.mark.xfail(
    strict=True, raises=NotImplementedError, reason="P4: measure not built yet"
)


def synthetic_aruco(
    marker_px: int = 200, canvas: tuple[int, int] = (600, 800)
) -> NDArray[np.uint8]:
    """White page with one DICT_4X4_50 id-0 marker of a known pixel size."""
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(dictionary, 0, marker_px)
    img = np.full(canvas, 255, dtype=np.uint8)
    img[100 : 100 + marker_px, 150 : 150 + marker_px] = marker
    return np.asarray(cv2.cvtColor(img, cv2.COLOR_GRAY2BGR), dtype=np.uint8)


def blank() -> NDArray[np.uint8]:
    return np.full((600, 800, 3), 255, dtype=np.uint8)


# ---------------------------------------------------------------- ArUco scale


def test_aruco_gives_mm_per_px() -> None:
    assert mm_per_px_from_aruco(synthetic_aruco(200), marker_mm=50.0) == pytest.approx(
        0.25, rel=0.02
    )


def test_aruco_larger_marker_smaller_scale() -> None:
    assert mm_per_px_from_aruco(synthetic_aruco(400), marker_mm=50.0) == pytest.approx(
        0.125, rel=0.02
    )


def test_aruco_default_marker_size_is_50mm() -> None:
    assert ARUCO_MARKER_MM == 50.0
    assert mm_per_px_from_aruco(synthetic_aruco(250)) == pytest.approx(0.2, rel=0.02)


def test_no_marker_returns_none() -> None:
    assert mm_per_px_from_aruco(blank()) is None


# ---------------------------------------------------------------- scale priority


def test_resolve_scale_prefers_aruco_over_inspector() -> None:
    scale, source = resolve_scale(synthetic_aruco(200), pdp_width_mm=100.0, pdp_px_width=500)
    assert source == ScaleSource.aruco
    assert scale == pytest.approx(0.25, rel=0.02)


def test_resolve_scale_falls_back_to_inspector() -> None:
    assert resolve_scale(blank(), pdp_width_mm=100.0, pdp_px_width=1000) == (
        0.1,
        ScaleSource.inspector,
    )


def test_resolve_scale_none_is_honest() -> None:
    assert resolve_scale(blank(), pdp_width_mm=None, pdp_px_width=None) == (None, ScaleSource.none)


# ---------------------------------------------------------------- Rule 7 Table I


@pytest.mark.parametrize(
    ("area", "embossed", "expected"),
    [
        (50, False, 1.0),
        (100, False, 1.0),
        (100.1, False, 2.0),
        (500, False, 2.0),
        (500.1, False, 4.0),
        (2500, False, 4.0),
        (2500.1, False, 6.0),
        (50, True, 2.0),
        (300, True, 4.0),
        (1000, True, 6.0),
        (3000, True, 8.0),
    ],
)
def test_table1_thresholds(area: float, embossed: bool, expected: float) -> None:
    assert min_height_mm(area, embossed) == expected


def test_pdp_area_rectangle() -> None:
    assert pdp_area_cm2(100.0, 50.0) == 50.0


def test_text_height() -> None:
    assert text_height_mm(40, 0.05) == pytest.approx(2.0)


# ---------------------------------------------------------------- width / height ratio


@pytest.mark.parametrize(
    ("width", "height", "text", "ok"),
    [
        (1.0, 3.0, "5", True),
        (0.9, 3.0, "5", False),
        (0.5, 3.0, "1", True),
        (0.5, 3.0, "l", True),
        (0.5, 3.0, "il1", True),
        (0.5, 3.0, "1a", False),
    ],
)
def test_width_ratio(width: float, height: float, text: str, ok: bool) -> None:
    assert width_ratio_ok(width, height, text) is ok
