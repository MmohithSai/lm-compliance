"""OpenCV preprocessing: light denoise. Returns a new image, never mutates the input."""

from __future__ import annotations

from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray


def preprocess(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Knock JPEG noise off a phone photo while keeping glyph edges sharp.

    Coordinates are left alone on purpose. No deskew: PP-OCRv4 detects rotated quads by
    itself, and rotating the page would put every box in a space the scan detail page cannot
    draw in (the axis-aligned box of a rotated line inflates by its own length).

    CLAHE on the lightness channel after the denoise: half the real photo set is white print on
    a curved coloured bottle under a ceiling light, where the whole panel sits in a narrow band
    of the histogram and PP-OCR's detector misses whole lines. Equalising locally (8x8 tiles)
    pulls those lines apart without touching hue, and the clip limit keeps it from turning JPEG
    grain into edges. Tuning knobs for the real photo set: the two sigmas, and the clip limit.
    """
    denoised = cv2.bilateralFilter(img, 5, 40, 40)
    lightness, a, b = cv2.split(cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB))
    lightness = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lightness)
    merged = cv2.cvtColor(cv2.merge((lightness, a, b)), cv2.COLOR_LAB2BGR)
    return cast("NDArray[np.uint8]", merged)
