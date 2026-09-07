"""OpenCV preprocessing (P2): deskew, denoise. Returns a new image, never mutates the input."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def preprocess(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
    raise NotImplementedError("P2")
