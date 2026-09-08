"""Scale detection, Rule 7 geometry, and what a printed line measures (P4)."""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from numpy.typing import NDArray

from pipeline.measure import (
    ARUCO_MARKER_MM,
    CARD_MM,
    ink,
    measure_declarations,
    min_height_mm,
    mm_per_px_from_aruco,
    mm_per_px_from_card,
    pdp_area_cm2,
    resolve_scale,
    text_height_mm,
    width_ratio_ok,
)
from pipeline.models import Declaration, ScaleSource, Word


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


# ---------------------------------------------------------------- credit-card scale


def synthetic_card(long_px: int = 856, angle: float = 0.0) -> NDArray[np.uint8]:
    """White page with one ID-1 shaped dark rectangle, optionally turned on the page."""
    short_px = round(long_px * CARD_MM[1] / CARD_MM[0])
    img = np.full((900, 1400, 3), 255, dtype=np.uint8)
    box = cv2.boxPoints(((700, 450), (long_px, short_px), angle))
    cv2.fillPoly(img, [box.astype(np.int32)], (40, 40, 40))
    return np.asarray(img, dtype=np.uint8)


def test_card_gives_mm_per_px() -> None:
    assert mm_per_px_from_card(synthetic_card(856)) == pytest.approx(0.1, rel=0.03)


def test_card_found_when_the_card_is_turned() -> None:
    assert mm_per_px_from_card(synthetic_card(856, angle=20)) == pytest.approx(0.1, rel=0.05)


def test_a_square_is_not_a_card() -> None:
    img = np.full((900, 1400, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (300, 200), (900, 800), (40, 40, 40), -1)
    assert mm_per_px_from_card(np.asarray(img, dtype=np.uint8)) is None


def test_no_card_returns_none() -> None:
    assert mm_per_px_from_card(blank()) is None


def test_resolve_scale_prefers_the_marker_over_the_card() -> None:
    img = synthetic_card(856)
    marker = cv2.aruco.generateImageMarker(
        cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), 0, 100
    )
    img[50:150, 50:150] = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
    scale, source = resolve_scale(np.asarray(img, dtype=np.uint8), None, None)
    assert source == ScaleSource.aruco
    assert scale == pytest.approx(0.5, rel=0.03)


def test_resolve_scale_falls_back_to_the_card() -> None:
    scale, source = resolve_scale(synthetic_card(856), pdp_width_mm=100.0, pdp_px_width=1400)
    assert source == ScaleSource.card
    assert scale == pytest.approx(0.1, rel=0.03)


# ---------------------------------------------------------------- what one printed line is


def printed(text: str, scale: float = 1.0, thickness: int = 2) -> NDArray[np.uint8]:
    """One line of black print on white, filling the crop the way an OCR box does."""
    (w, h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    img = np.full((h + baseline + 8, w + 8, 3), 255, dtype=np.uint8)
    cv2.putText(img, text, (4, h + 4), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness)
    return np.asarray(img, dtype=np.uint8)


def test_ink_measures_the_glyphs_not_the_box() -> None:
    """The box is padded and spans a whole line; Rule 7 measures the capitals in it."""
    crop = printed("MRP 20.00")
    (_w, cap), _baseline = cv2.getTextSize("MRP 20.00", cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
    measured = ink(crop)
    assert measured is not None
    assert measured.height_px < crop.shape[0]
    # Hershey's reported text height carries padding the print does not, hence the slack.
    assert measured.height_px == pytest.approx(cap, rel=0.3)
    assert measured.contrast > 0.8
    assert measured.width_height_ratio > 0.33


def test_ink_reads_white_print_on_a_dark_pack() -> None:
    crop = np.asarray(255 - printed("NET WT 200 g"), dtype=np.uint8)
    measured = ink(crop)
    assert measured is not None
    assert measured.contrast > 0.8


def test_ink_of_blank_paper_is_none() -> None:
    assert ink(np.full((40, 200, 3), 255, dtype=np.uint8)) is None


# ---------------------------------------------------------------- declarations


def page_with_one_line(text: str) -> tuple[NDArray[np.uint8], Word]:
    line = printed(text)
    page = np.full((400, 900, 3), 255, dtype=np.uint8)
    h, w = line.shape[:2]
    page[100 : 100 + h, 60 : 60 + w] = line
    word = Word(id=1, image_id="img-a", text=text, x=60, y=100, w=w, h=h, confidence=0.9)
    return np.asarray(page, dtype=np.uint8), word


def test_measure_declarations_fills_height_ratio_and_contrast() -> None:
    page, word = page_with_one_line("MRP 20.00")
    decl = Declaration(field="mrp", value="MRP 20.00", word_ids=[1], image_id="img-a")
    (measured,) = measure_declarations([decl], [word], {"img-a": page}, {"img-a": 0.1})
    assert measured.height_mm is not None and 1.5 < measured.height_mm < 3.0  # ~22 px cap x 0.1
    assert measured.width_height_ratio is not None and measured.width_height_ratio > 0.33
    assert measured.contrast is not None and measured.contrast > 0.8


def test_measure_declarations_without_a_scale_measures_nothing() -> None:
    """Not even contrast. A photo shot without a reference in the frame reports the light and
    the focus: 54% of the real declaration lines in eval/dataset came out under the 0.5 floor,
    and the worst of them is a shadow across a bottle."""
    page, word = page_with_one_line("MRP 20.00")
    decl = Declaration(field="mrp", value="MRP 20.00", word_ids=[1], image_id="img-a")
    (measured,) = measure_declarations([decl], [word], {"img-a": page}, {"img-a": None})
    assert measured.height_mm is None
    assert measured.width_height_ratio is None
    assert measured.contrast is None


def test_measure_declarations_leaves_an_unphotographed_declaration_alone() -> None:
    decl = Declaration(field="mrp", value="MRP 20.00", word_ids=[], image_id=None)
    (measured,) = measure_declarations([decl], [], {}, {})
    assert (measured.height_mm, measured.width_height_ratio, measured.contrast) == (
        None,
        None,
        None,
    )


def test_a_card_is_only_a_card_when_the_inspector_says_one_is_there() -> None:
    """A rectangle identifies nothing. Measured on the eval set, the card detector claimed a
    scale in 14 frames with no card in them; a marker's bits are error-corrected, a shape is not."""
    assert resolve_scale(synthetic_card(856), None, None, look_for_card=False) == (
        None,
        ScaleSource.none,
    )


def test_contrast_sees_colour_not_only_brightness() -> None:
    """Red print on green is legible and has almost no difference in brightness. Luminance alone
    called every real photograph in the eval set low-contrast; Lab distance does not."""
    crop = np.full((40, 200, 3), (0, 128, 0), dtype=np.uint8)  # green paper
    cv2.putText(crop, "200 g", (4, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2)  # red print
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    measured = ink(np.asarray(crop, dtype=np.uint8))
    assert measured is not None
    assert abs(int(gray.max()) - int(gray.min())) < 60  # barely any brightness difference
    assert measured.contrast > 0.5
