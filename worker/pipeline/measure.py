"""Scale and font geometry (P4). Never invents a measurement: None means "not verifiable".

Three things are measured here, and all three are measured on the photograph as uploaded, not
on the preprocessed copy: `preprocess` runs CLAHE, and equalising a crop and then reporting its
contrast measures the equalisation. `preprocess` never moves a pixel, so an OCR box drawn on the
preprocessed page indexes the raw page as well.

What a measurement costs when it is wrong is asymmetric: a height that is too small accuses a
compliant pack. So every estimate here is taken from the print itself (the ink inside the OCR
box, not the box) and, where a choice remained, the reading that does not accuse was taken.
"""

from __future__ import annotations

from statistics import median
from typing import NamedTuple, cast

import cv2
import numpy as np
from numpy.typing import NDArray

from .models import Declaration, ScaleSource, Word

ARUCO_DICT_NAME = "DICT_4X4_50"
ARUCO_MARKER_MM = 50.0  # printed reference card: one 50 mm marker
CARD_MM = (85.6, 54.0)  # ISO/IEC 7810 ID-1 (credit card)
RATIO_EXEMPT_CHARS = set("1iIl")  # Rule 7: width >= 1/3 height except these
MIN_RATIO = 1 / 3

# Rule 7, Table I: minimum height of the numerals by principal display panel area.
# (area is at most, mm normally, mm when raised, embossed or perforated)
TABLE_I: list[tuple[float, float, float]] = [
    (100.0, 1.0, 2.0),
    (500.0, 2.0, 4.0),
    (2500.0, 4.0, 6.0),
    (float("inf"), 6.0, 8.0),
]

# A quadrilateral counts as the reference card when its long/short side is within this much of
# 85.6/54. The slack is perspective: a card photographed off-square reads narrower than it is.
CARD_ASPECT = CARD_MM[0] / CARD_MM[1]
CARD_ASPECT_SLACK = 0.12
CARD_MIN_AREA_FRACTION = 0.002  # smaller than this and the "card" is a logo or a barcode

# A connected blob shorter than this fraction of the line's ink is a dot, a comma or JPEG grain,
# not a glyph.
GLYPH_MIN_HEIGHT = 0.4


def mm_per_px_from_aruco(
    img: NDArray[np.uint8], marker_mm: float = ARUCO_MARKER_MM
) -> float | None:
    """Millimetres per pixel from a DICT_4X4_50 marker, or None if there is no marker."""
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    corners, _ids, _rejected = cv2.aruco.ArucoDetector(dictionary).detectMarkers(img)
    # Every side of every marker found. The median survives one corner the detector placed badly
    # and a marker photographed at an angle, where two sides are foreshortened and two are not.
    sides = [
        float(np.linalg.norm(quad[0][i] - quad[0][(i + 1) % 4]))
        for quad in corners
        for i in range(4)
    ]
    return marker_mm / median(sides) if sides else None


def mm_per_px_from_card(img: NDArray[np.uint8]) -> float | None:
    """Millimetres per pixel from a credit-card-shaped rectangle, or None if there is none.

    The largest quadrilateral with ID-1 proportions wins: a card is put in the frame to be
    measured, so it is a big object, and the runners-up are usually a barcode or the pack itself.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    # Dilate before contouring: a printed card's border is broken by the print on it, and a
    # broken border is several contours, none of which is a quadrilateral.
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    longest = 0.0
    for contour in contours:
        if cv2.contourArea(contour) < CARD_MIN_AREA_FRACTION * gray.size:
            continue
        quad = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(quad) != 4 or not cv2.isContourConvex(quad):
            continue
        long_px, short_px = sorted(cv2.minAreaRect(quad)[1], reverse=True)
        if short_px <= 0 or abs(long_px / short_px - CARD_ASPECT) > CARD_ASPECT_SLACK * CARD_ASPECT:
            continue
        longest = max(longest, long_px)
    return CARD_MM[0] / longest if longest else None


def resolve_scale(
    img: NDArray[np.uint8],
    pdp_width_mm: float | None,
    pdp_px_width: int | None,
    look_for_card: bool = True,
) -> tuple[float | None, ScaleSource]:
    """Priority: ArUco -> card -> inspector PDP mm -> (None, ScaleSource.none).

    The card is only looked for when the inspector said one is in the frame. A marker identifies
    itself — the bits are error-corrected — but a rectangle does not, and measured on the eval set
    the card detector claimed a scale in 14 frames that contain no card: product photos on a
    listing, a label panel, the flat side of a carton. A wrong scale is worse than no scale, so
    the inspector's answer, which the upload form already asks for, gates it.
    """
    marker = mm_per_px_from_aruco(img)
    if marker is not None:
        return marker, ScaleSource.aruco
    card = mm_per_px_from_card(img) if look_for_card else None
    if card is not None:
        return card, ScaleSource.card
    if pdp_width_mm and pdp_px_width:
        return pdp_width_mm / pdp_px_width, ScaleSource.inspector
    return None, ScaleSource.none


def pdp_area_cm2(width_mm: float, height_mm: float) -> float:
    """Rule 8, rectangular packages only (cylinders are out of scope for the MVP)."""
    return width_mm * height_mm / 100


def min_height_mm(pdp_area_cm2: float, embossed: bool = False) -> float:
    """Rule 7 Table-I."""
    for limit, normal, raised in TABLE_I:
        if pdp_area_cm2 <= limit:
            return raised if embossed else normal
    raise AssertionError("Table I's last row has no upper limit")  # pragma: no cover


def text_height_mm(word_h_px: int, mm_per_px: float) -> float:
    return word_h_px * mm_per_px


def width_ratio_ok(char_width_mm: float, height_mm: float, text: str) -> bool:
    """Rule 7: numeral/letter width >= 1/3 of height, except 1, i, I, l."""
    if not set(text) - RATIO_EXEMPT_CHARS:
        return True
    return char_width_mm / height_mm >= MIN_RATIO


# ---------------------------------------------------------------- measuring the print itself


class Ink(NamedTuple):
    """What one printed line is, measured inside its OCR box."""

    height_px: float  # tall glyphs: the capitals and numerals Rule 7 measures
    width_height_ratio: float
    contrast: float  # 0..1, ink against the paper right beside it


def _core(mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """The mask without its one-pixel border, or the mask itself when it is all border."""
    eroded = cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    return cast("NDArray[np.bool_]", eroded if eroded.any() else mask)


def ink(crop: NDArray[np.uint8]) -> Ink | None:
    """Measure one line box. None when there is no print in it to measure.

    The OCR box is the detector's box, not the print: it is padded, and it spans a whole line, so
    its height is ascender-to-descender at best. Rule 7 measures the height of the numerals and
    capitals, so the glyphs are found inside the box and the tall ones are measured.

    Contrast is ink against paper *in the same crop*, so the lighting is common to both sides of
    the comparison and largely cancels. That is what makes it a property of the pack and not of
    the photograph — which the raw-image rule above is the other half of. It is measured in
    colour, as CIE Lab distance over 100: a pack printing red on green is perfectly legible and
    has almost no difference in brightness, and a luminance-only reading called 27 of the 27 real
    photographs low-contrast (eval/results/2026-09-08_p4-measure-wired.json). Rule 9(1)(a) asks
    for print "in contrast with the background", not for print that is darker than it.
    """
    if crop.ndim == 2:
        crop = cast("NDArray[np.uint8]", cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR))
    if crop.size == 0 or min(crop.shape[:2]) < 3:
        return None
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _threshold, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Otsu splits the crop in two. Print covers less of a line than its background does, so the
    # smaller half is the ink — which is also how white-on-dark print is read without a flag.
    dark = binary == 0
    is_ink = dark if int(dark.sum()) <= int((~dark).sum()) else ~dark
    if not is_ink.any() or is_ink.all():
        return None

    rows = np.flatnonzero(is_ink.any(axis=1))
    line_px = float(rows[-1] - rows[0] + 1)
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(
        is_ink.astype(np.uint8), connectivity=8
    )
    glyphs = [
        (float(stats[i, cv2.CC_STAT_WIDTH]), float(stats[i, cv2.CC_STAT_HEIGHT]))
        for i in range(1, count)
        if stats[i, cv2.CC_STAT_HEIGHT] >= GLYPH_MIN_HEIGHT * line_px
    ]
    if not glyphs:
        return None
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float64)
    # OpenCV packs 8-bit Lab as L*255/100 and a/b + 128; undo that so the distance is in CIE units.
    lab = lab * (100 / 255, 1, 1) - (0, 128, 128)
    # The core of the stroke and the paper away from it. A glyph's edge pixels are half ink and
    # half paper, and on small print most pixels are edge: measured on the rendered labels, whose
    # print is pure black on white, the edges dragged a true 1.0 down to 0.87.
    ink_lab, paper_lab = (lab[_core(mask)].mean(axis=0) for mask in (is_ink, ~is_ink))
    contrast = min(float(np.linalg.norm(ink_lab - paper_lab)) / 100, 1.0)
    return Ink(
        # The tall glyphs, not all of them: Table I measures the numerals, and a line's x-height
        # blobs would report a lower-case 'a' as their height and accuse a pack that prints them
        # full size. Measured on the marker cases, the 75th percentile read a line of mostly
        # lower-case as 2.26 mm where its capitals are 3.13 mm; the 90th reads the capitals. Not
        # the tallest glyph: one OCR box that swallowed a logo would then set the height.
        height_px=float(np.percentile([h for _w, h in glyphs], 90)),
        # Per glyph, then the median: glyph shapes differ ('I' against 'M'), and Rule 7 is about
        # a condensed typeface, which shows in the middle of that spread, not in one letter.
        width_height_ratio=median(w / h for w, h in glyphs),
        contrast=contrast,
    )


def measure_declarations(
    decls: list[Declaration],
    words: list[Word],
    pages: dict[str, NDArray[np.uint8]],
    scale: dict[str, float | None],
) -> list[Declaration]:
    """Fill height_mm, width_height_ratio and contrast on every declaration that can carry them.

    A declaration is one or more printed lines. Each is measured on its own and the median is
    taken, so one OCR box that swallowed a rule line or a logo cannot decide the verdict.

    All three need `scale[image_id]`, and not only because two of them are in millimetres. A
    photograph shot without a reference in the frame is not evidence about contrast either:
    measured over the eval set, 54% of the declaration lines on real photographs came out under
    the 0.5 floor, and the crops behind the worst of them are a shadow across a Sprite bottle and
    a pale blue line that is perfectly legible on the carton
    (eval/results/2026-09-08_p4-contrast-in-colour.json). That number is the light and the focus,
    not the print. With no scale the three stay None and F1, F2 and P2 report "not verifiable".
    """
    boxes = {w.id: w for w in words}
    out = []
    for decl in decls:
        lines = [boxes[i] for i in decl.word_ids if i in boxes]
        measured = [
            m
            for w in lines
            if w.image_id in pages
            and (m := ink(pages[w.image_id][w.y : w.y + w.h, w.x : w.x + w.w])) is not None
        ]
        if not measured:
            out.append(decl)
            continue
        mm_per_px = scale.get(lines[0].image_id)
        if mm_per_px is None:
            out.append(decl)
            continue
        height = median(m.height_px for m in measured)
        update: dict[str, float] = {
            "height_mm": round(text_height_mm(int(round(height)), mm_per_px), 2),
            "width_height_ratio": round(median(m.width_height_ratio for m in measured), 2),
            "contrast": round(median(m.contrast for m in measured), 2),
        }
        out.append(decl.model_copy(update=cast("dict[str, object]", update)))
    return out
