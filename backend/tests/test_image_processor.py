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


def test_extremely_wide_image_keeps_nonzero_resize_height(monkeypatch) -> None:
    image = np.zeros((1, 100_000, 3), dtype=np.uint8)
    monkeypatch.setattr(cv2, "imread", lambda *_args, **_kwargs: image)

    prepared = ImageProcessor(64).prepare(Path("wide.png"))

    assert prepared.width == 100_000
    assert prepared.height == 1
    assert prepared.tensor.shape == (3, 64, 64)


def test_extremely_tall_image_keeps_nonzero_resize_width(monkeypatch) -> None:
    image = np.zeros((100_000, 1, 3), dtype=np.uint8)
    monkeypatch.setattr(cv2, "imread", lambda *_args, **_kwargs: image)

    prepared = ImageProcessor(64).prepare(Path("tall.png"))

    assert prepared.width == 1
    assert prepared.height == 100_000
    assert prepared.tensor.shape == (3, 64, 64)
