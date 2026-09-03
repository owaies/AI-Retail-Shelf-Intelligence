from pathlib import Path

import cv2
import numpy as np

from app.services.image_processor import ImageProcessor


def test_opencv_preprocessing_letterboxes_image(tmp_path: Path) -> None:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    path = tmp_path / "image.jpg"
    assert cv2.imwrite(str(path), image)

    prepared = ImageProcessor(416).prepare(path)

    assert prepared.width == 200
    assert prepared.height == 100
    assert prepared.tensor.shape == (3, 416, 416)
    assert prepared.tensor.dtype == np.float32
    assert prepared.ratio == 416 / 200
