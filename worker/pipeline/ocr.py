"""PaddleOCR wrapper (P2). PP-OCRv4, English by default; Devanagari via OCR_LANGS=en,hi."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .models import Word


def ocr_words(img: NDArray[np.uint8], image_id: str, langs: list[str]) -> list[Word]:
    """Word-level boxes with confidence. Ids are unique per scan (caller offsets them)."""
    raise NotImplementedError("P2")
