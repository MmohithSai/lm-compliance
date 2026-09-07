"""PaddleOCR wrapper. PP-OCRv4. The model follows ScanContext.languages, English by default.

One Word is one detected text box, and PP-OCR detects at line level. A line is never split
into per-word boxes: the split coordinates would be invented, and this project does not invent
measurements. The extractor and the font checks both work off whole lines.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .models import Word

# PP-OCR ships one recognition model per script. The Devanagari model also reads Latin and
# digits, so a bilingual Hindi/English pack needs one pass, not two.
PADDLE_LANG = {"hi": "devanagari", "mr": "devanagari", "ne": "devanagari"}


@lru_cache(maxsize=2)
def engine(lang: str) -> Any:
    """One PaddleOCR per script. Loading the models takes seconds, so they are kept."""
    from paddleocr import PaddleOCR  # heavy, and only installed with `--extra ocr`

    return PaddleOCR(lang=lang, use_angle_cls=True, show_log=False)


def paddle_lang(langs: list[str]) -> str:
    return next((PADDLE_LANG[c] for c in langs if c in PADDLE_LANG), "en")


def ocr_words(img: NDArray[np.uint8], image_id: str, langs: list[str]) -> list[Word]:
    """Line-level boxes with confidence. Ids are unique per image (caller offsets them)."""
    pages: list[list[Any]] | None = engine(paddle_lang(langs)).ocr(img, cls=True)
    words: list[Word] = []
    for quad, (text, confidence) in (pages or [[]])[0] or []:
        if not text.strip():
            continue
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]
        words.append(
            Word(
                id=len(words),
                image_id=image_id,
                text=text.strip(),
                x=int(min(xs)),
                y=int(min(ys)),
                w=int(max(xs) - min(xs)),
                h=int(max(ys) - min(ys)),
                confidence=float(confidence),
            )
        )
    return words
