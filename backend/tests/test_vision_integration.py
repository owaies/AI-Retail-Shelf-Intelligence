import os
import tempfile
from pathlib import Path
from urllib.request import urlopen

import pytest

from app.services.vision import VisionService


@pytest.mark.skipif(os.getenv("RUN_CV_INTEGRATION") != "1", reason="CV integration test requires model/image download")
def test_real_yolox_inference_on_pinned_yolox_sample() -> None:
    url = "https://raw.githubusercontent.com/Megvii-BaseDetection/YOLOX/6ddff4824372906469a7fae2dc3206c7aa4bbaee/assets/dog.jpg"
    with tempfile.TemporaryDirectory() as directory:
        image_path = Path(directory) / "dog.jpg"
        with urlopen(url, timeout=30) as response:
            image_path.write_bytes(response.read())
        result = VisionService().analyze(str(image_path))

    assert result.width > 0 and result.height > 0
    assert result.detections, "YOLOX returned no detections for the official sample image"
    assert any(d.class_name == "dog" and d.confidence >= 0.25 for d in result.detections)
