from __future__ import annotations

import random
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import yaml

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def parse_yolo_label_line(line: str, width: int = 1, height: int = 1) -> tuple[float, float, float, float, int] | None:
    """Parse either standard 5-element YOLO box or polygon segmentation to [x1, y1, x2, y2, cls_id]."""
    parts = line.strip().split()
    if not parts:
        return None
    cls_id = int(parts[0])
    nums = [float(p) for p in parts[1:]]

    if len(nums) == 4:
        xc, yc, w, h = nums
        x1 = (xc - w / 2) * width
        y1 = (yc - h / 2) * height
        x2 = (xc + w / 2) * width
        y2 = (yc + h / 2) * height
    elif len(nums) >= 6 and len(nums) % 2 == 0:
        xs = nums[0::2]
        ys = nums[1::2]
        x1 = min(xs) * width
        x2 = max(xs) * width
        y1 = min(ys) * height
        y2 = max(ys) * height
    else:
        return None

    return (x1, y1, x2, y2, cls_id)


def validate_retail_dataset(dataset_dir: Path | str) -> dict:
    """Validate that dataset conforms strictly to expected YOLO retail format."""
    path = Path(dataset_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"Dataset root directory not found: {path}")

    yaml_path = path / "data.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Missing data.yaml in {path}")

    with yaml_path.open("r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    if not isinstance(meta, dict):
        raise ValueError(f"Invalid data.yaml in {yaml_path}: expected dictionary mapping")

    names = meta.get("names", [])
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names.keys())]

    nc = meta.get("nc", len(names))
    if len(names) != 62 or nc != 62:
        raise ValueError(f"Expected exactly 62 classes in data.yaml, but found nc={nc}, len(names)={len(names)}")

    split_counts = {}
    for split_name in ("train", "valid", "test"):
        split_dir = path / split_name
        img_dir = split_dir / "images"
        lbl_dir = split_dir / "labels"

        if not img_dir.is_dir():
            raise FileNotFoundError(f"Missing images directory for split: {img_dir}")
        if not lbl_dir.is_dir():
            raise FileNotFoundError(f"Missing labels directory for split: {lbl_dir}")

        images = [p for p in img_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
        labels = list(lbl_dir.glob("*.txt"))
        if not images:
            raise ValueError(f"No valid images found in {img_dir}")

        # Spot-check labels in split
        for lbl_path in labels[:100]:
            lines = lbl_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line_no, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                parsed = parse_yolo_label_line(line, width=1, height=1)
                if parsed is None:
                    raise ValueError(f"Malformed label in {lbl_path}:{line_no}: {line}")
                x1, y1, x2, y2, cls_id = parsed
                if not 0 <= cls_id < 62:
                    raise ValueError(f"Invalid class ID {cls_id} in {lbl_path}:{line_no}. Expected [0, 61]")
                if x1 < 0.0 or y1 < 0.0 or x2 > 1.05 or y2 > 1.05:
                    raise ValueError(f"Unnormalized coordinates in {lbl_path}:{line_no}: ({x1}, {y1}, {x2}, {y2})")

        split_counts[split_name] = {
            "images": len(images),
            "labels": len(labels),
        }

    return {
        "status": "valid",
        "dataset_path": str(path),
        "num_classes": nc,
        "class_names": list(names),
        "splits": split_counts,
    }


class YoloRetailDataset(Dataset):
    """PyTorch Dataset loading YOLO-annotated retail images for YOLOX training."""

    def __init__(
        self,
        img_dir: Path | str,
        lbl_dir: Path | str,
        img_size: int = 640,
        augment: bool = False,
        num_classes: int = 62,
    ) -> None:
        self.img_dir = Path(img_dir)
        self.lbl_dir = Path(lbl_dir)
        self.img_size = (img_size, img_size)
        self.augment = augment
        self.num_classes = num_classes

        self.img_paths = sorted(
            [p for p in self.img_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
        )
        if not self.img_paths:
            raise ValueError(f"No supported images found in {self.img_dir}")

    def __len__(self) -> int:
        return len(self.img_paths)

    def _load_labels(self, img_path: Path, width: int, height: int) -> np.ndarray:
        lbl_path = self.lbl_dir / f"{img_path.stem}.txt"
        if not lbl_path.exists():
            return np.zeros((0, 5), dtype=np.float32)

        boxes = []
        for line in lbl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            parsed = parse_yolo_label_line(line, width, height)
            if parsed is not None:
                x1, y1, x2, y2, cls_id = parsed
                boxes.append([x1, y1, x2, y2, float(cls_id)])

        if not boxes:
            return np.zeros((0, 5), dtype=np.float32)
        return np.array(boxes, dtype=np.float32)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, tuple[int, int], int]:
        img_path = self.img_paths[index]
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Failed to read image at {img_path}")

        h, w = img.shape[:2]
        boxes = self._load_labels(img_path, w, h)

        # Letterbox resizing (fill with 114, matching YOLOX)
        target_h, target_w = self.img_size
        padded = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
        ratio = min(target_h / h, target_w / w)
        resized_w = int(w * ratio)
        resized_h = int(h * ratio)
        resized = cv2.resize(img, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
        padded[:resized_h, :resized_w] = resized

        # Adjust bounding boxes to letterboxed coordinates
        if len(boxes) > 0:
            boxes[:, 0:4] *= ratio
            boxes[:, 0] = np.clip(boxes[:, 0], 0, target_w)
            boxes[:, 2] = np.clip(boxes[:, 2], 0, target_w)
            boxes[:, 1] = np.clip(boxes[:, 1], 0, target_h)
            boxes[:, 3] = np.clip(boxes[:, 3], 0, target_h)

        # Data augmentation
        if self.augment and random.random() < 0.5:
            # Horizontal flip
            padded = np.ascontiguousarray(np.fliplr(padded))
            if len(boxes) > 0:
                x1 = target_w - boxes[:, 2]
                x2 = target_w - boxes[:, 0]
                boxes[:, 0] = x1
                boxes[:, 2] = x2

        # Convert to BGR float32 tensor [3, H, W] in [0, 255] (YOLOX convention)
        tensor = torch.from_numpy(padded.transpose(2, 0, 1)).float()
        targets = torch.from_numpy(boxes).float()

        return tensor, targets, (h, w), index


def yolox_collate_fn(batch: list[tuple[torch.Tensor, torch.Tensor, tuple[int, int], int]]):
    images, targets, img_sizes, img_ids = zip(*batch)
    stacked_images = torch.stack(images, dim=0)

    # Pad targets to max_labels for batched processing
    max_targets = max((len(t) for t in targets), default=0)
    padded_targets = torch.zeros((len(targets), max(max_targets, 1), 5), dtype=torch.float32)
    for i, t in enumerate(targets):
        if len(t) > 0:
            padded_targets[i, :len(t)] = t

    return stacked_images, padded_targets, img_sizes, img_ids
