from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class PreparedImage:
    tensor: np.ndarray
    width: int
    height: int
    ratio: float
    input_size: tuple[int, int]


class ImageProcessor:
    """Decode and letterbox an image using the preprocessing used by YOLOX."""

    def __init__(self, input_size: int = 416) -> None:
        self.input_size = (input_size, input_size)

    def prepare(self, image_path: Path) -> PreparedImage:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Uploaded file is not a decodable image")
        height, width = image.shape[:2]
        if width < 1 or height < 1:
            raise ValueError("Image has invalid dimensions")

        padded = np.full((*self.input_size, 3), 114, dtype=np.uint8)
        ratio = min(self.input_size[0] / height, self.input_size[1] / width)
        resized_w = int(width * ratio)
        resized_h = int(height * ratio)
        resized = cv2.resize(image, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
        padded[:resized_h, :resized_w] = resized
        tensor = np.ascontiguousarray(padded.transpose(2, 0, 1), dtype=np.float32)
        return PreparedImage(tensor=tensor, width=width, height=height, ratio=ratio, input_size=self.input_size)

    @staticmethod
    def decode_bytes(data: bytes) -> np.ndarray:
        array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Uploaded file is not a decodable image")
        return image

    @staticmethod
    def image_dimensions(path: Path) -> tuple[int, int]:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Image cannot be decoded")
        height, width = image.shape[:2]
        return width, height
