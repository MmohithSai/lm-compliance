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
    Tuning knobs for the real photo set: the two sigmas below, and CLAHE if glare shows up.
    """
    return cast("NDArray[np.uint8]", cv2.bilateralFilter(img, 5, 40, 40))
