from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from app.training.dataset import (
    YoloRetailDataset,
    parse_yolo_label_line,
    validate_retail_dataset,
    yolox_collate_fn,
)
from app.training.loss import YOLOXLoss
from app.training.models.yolox import (
    CSPDarknet,
    YOLOPAFPN,
    YOLOX,
    YOLOXHead,
    create_yolox_s,
)


def test_parse_yolo_label_line_standard():
    line = "5 0.5 0.5 0.2 0.4"
    parsed = parse_yolo_label_line(line, width=100, height=100)
    assert parsed is not None
    x1, y1, x2, y2, cls_id = parsed
    assert cls_id == 5
    assert pytest.approx(x1, 1e-4) == 40.0
    assert pytest.approx(y1, 1e-4) == 30.0
    assert pytest.approx(x2, 1e-4) == 60.0
    assert pytest.approx(y2, 1e-4) == 70.0


def test_parse_yolo_label_line_polygon():
    # Polygon with 4 vertices (x,y)
    line = "12 0.1 0.2 0.3 0.2 0.3 0.8 0.1 0.8"
    parsed = parse_yolo_label_line(line, width=1000, height=1000)
    assert parsed is not None
    x1, y1, x2, y2, cls_id = parsed
    assert cls_id == 12
    assert pytest.approx(x1, 1e-4) == 100.0
    assert pytest.approx(y1, 1e-4) == 200.0
    assert pytest.approx(x2, 1e-4) == 300.0
    assert pytest.approx(y2, 1e-4) == 800.0


def test_parse_yolo_label_line_invalid():
    assert parse_yolo_label_line("") is None
    assert parse_yolo_label_line("   ") is None
    assert parse_yolo_label_line("1 0.5 0.5") is None  # Odd length / fewer than 4


def test_validate_retail_dataset_nonexistent():
    with pytest.raises(FileNotFoundError):
        validate_retail_dataset("/nonexistent/dataset/path")


def test_validate_retail_dataset_synthetic(tmp_path: Path):
    ds_dir = tmp_path / "mock_dataset"
    ds_dir.mkdir()

    # Create data.yaml with 62 classes
    names = [f"item_{i}" for i in range(62)]
    data_yaml = ds_dir / "data.yaml"
    data_yaml.write_text(f"nc: 62\nnames:\n" + "\n".join(f"  - {n}" for n in names))

    # Create train, valid, test splits
    for split in ("train", "valid", "test"):
        img_dir = ds_dir / split / "images"
        lbl_dir = ds_dir / split / "labels"
        img_dir.mkdir(parents=True)
        lbl_dir.mkdir(parents=True)

        # Create dummy image and label
        (img_dir / "0001.jpg").write_bytes(b"dummy")
        (lbl_dir / "0001.txt").write_text("0 0.5 0.5 0.2 0.2\n61 0.3 0.3 0.1 0.1")

    res = validate_retail_dataset(ds_dir)
    assert res["status"] == "valid"
    assert res["num_classes"] == 62
    assert len(res["class_names"]) == 62
    assert res["splits"]["train"]["images"] == 1


def test_validate_retail_dataset_wrong_class_count(tmp_path: Path):
    ds_dir = tmp_path / "mock_bad_classes"
    ds_dir.mkdir()
    data_yaml = ds_dir / "data.yaml"
    data_yaml.write_text("nc: 10\nnames:\n" + "\n".join(f"  - item_{i}" for i in range(10)))

    with pytest.raises(ValueError, match="Expected exactly 62 classes"):
        validate_retail_dataset(ds_dir)


def test_yolox_s_model_architecture():
    model = create_yolox_s(num_classes=62, pretrained=False, device="cpu")
    model.eval()

    dummy_input = torch.zeros(2, 3, 640, 640)
    with torch.no_grad():
        out = model(dummy_input)

    # 640x640 with strides (8, 16, 32):
    # 80x80 (6400) + 40x40 (1600) + 20x20 (400) = 8400 anchor predictions
    # Output channels = 4 (reg) + 1 (obj) + 62 (classes) = 67
    assert out.shape == (2, 8400, 67)


def test_yolox_loss_computation():
    loss_fn = YOLOXLoss(num_classes=62)
    predictions = torch.randn(2, 8400, 67)
    # Targets: 2 images, 3 targets each: [x1, y1, x2, y2, class_id]
    targets = torch.tensor(
        [
            [
                [50.0, 50.0, 150.0, 150.0, 0.0],
                [200.0, 200.0, 300.0, 300.0, 15.0],
                [0.0, 0.0, 0.0, 0.0, 0.0],
            ],
            [
                [100.0, 100.0, 250.0, 250.0, 61.0],
                [0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0],
            ],
        ],
        dtype=torch.float32,
    )

    loss, metrics = loss_fn(predictions, targets, img_size=(640, 640))
    assert isinstance(loss, torch.Tensor)
    assert not torch.isnan(loss).item()
    assert not torch.isinf(loss).item()
    assert loss.item() > 0
    assert "loss_total" in metrics
    assert "loss_iou" in metrics
    assert "loss_cls" in metrics
    assert "loss_obj" in metrics


def test_yolox_collate_fn():
    img1 = torch.zeros(3, 640, 640)
    img2 = torch.zeros(3, 640, 640)
    tgt1 = torch.tensor([[10.0, 10.0, 50.0, 50.0, 1.0]], dtype=torch.float32)
    tgt2 = torch.tensor(
        [[10.0, 10.0, 50.0, 50.0, 2.0], [60.0, 60.0, 100.0, 100.0, 3.0]],
        dtype=torch.float32,
    )

    batch = [
        (img1, tgt1, (640, 640), 0),
        (img2, tgt2, (640, 640), 1),
    ]

    stacked_imgs, padded_targets, img_sizes, img_ids = yolox_collate_fn(batch)
    assert stacked_imgs.shape == (2, 3, 640, 640)
    assert padded_targets.shape == (2, 2, 5)
    assert len(img_sizes) == 2
    assert img_ids == (0, 1)
