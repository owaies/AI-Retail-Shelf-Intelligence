from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.evaluation import GroundTruth, evaluate_dataset
from app.services.vision import BoundingBox, COCO_CLASSES, VisionService

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_ground_truth(label_path: Path, width: int, height: int) -> list[GroundTruth]:
    if not label_path.exists():
        return []
    truths: list[GroundTruth] = []
    for line_number, line in enumerate(label_path.read_text().splitlines(), start=1):
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{label_path}:{line_number}: expected class_id x_center y_center width height")
        class_id, x_center, y_center, box_width, box_height = fields
        class_index = int(class_id)
        if not 0 <= class_index < len(COCO_CLASSES):
            raise ValueError(f"{label_path}:{line_number}: invalid COCO class id {class_index}")
        box_width_px = float(box_width) * width
        box_height_px = float(box_height) * height
        truths.append(GroundTruth(
            class_name=COCO_CLASSES[class_index],
            box=BoundingBox(
                x=float(x_center) * width - box_width_px / 2,
                y=float(y_center) * height - box_height_px / 2,
                width=box_width_px,
                height=box_height_px,
            ),
        ))
    return truths


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the local YOLOX-S detector on YOLO-format labels.")
    parser.add_argument("dataset", type=Path, help="Dataset directory containing images/ and labels/")
    parser.add_argument("--iou", type=float, default=0.50, help="IoU threshold for matching (default: 0.50)")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    image_dir = args.dataset / "images"
    label_dir = args.dataset / "labels"
    if not image_dir.is_dir() or not label_dir.is_dir():
        raise SystemExit("Dataset must contain images/ and labels/ directories")

    service = VisionService()
    samples = []
    for image_path in sorted(image_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        width, height = service.processor.image_dimensions(image_path)
        predictions = service.analyze(str(image_path)).detections
        truths = load_ground_truth(label_dir / f"{image_path.stem}.txt", width, height)
        samples.append((predictions, truths))

    if not samples:
        raise SystemExit("No supported images found in dataset/images")

    metrics = evaluate_dataset(samples, iou_threshold=args.iou)
    report = {"iou_threshold": args.iou, **metrics.__dict__}
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
