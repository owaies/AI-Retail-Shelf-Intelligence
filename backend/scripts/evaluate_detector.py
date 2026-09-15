from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from app.services.evaluation import (
    DatasetVocabulary,
    EvaluationMetrics,
    GroundTruth,
    VocabularyMismatchError,
    evaluate_dataset,
)
from app.services.vision import BoundingBox, COCO_CLASSES, VisionService

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def find_data_yaml(target_path: Path) -> Path | None:
    """Attempt to locate data.yaml in the path or its parent directories."""
    candidates = [
        target_path / "data.yaml",
        target_path.parent / "data.yaml",
        target_path.parent.parent / "data.yaml",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resolve_dataset_directories(
    dataset_path: Path, split: str | None = None
) -> tuple[Path, Path, Path | None]:
    """Resolve (images_dir, labels_dir, data_yaml_path) from given dataset path."""
    yaml_path = find_data_yaml(dataset_path)

    # 1. Check if dataset_path itself contains images/ and labels/
    if (dataset_path / "images").is_dir() and (dataset_path / "labels").is_dir():
        return dataset_path / "images", dataset_path / "labels", yaml_path

    # 2. Check if a split was requested or exists (test > valid > train)
    splits_to_check = [split] if split else ["test", "valid", "val", "train"]
    for s in splits_to_check:
        if not s:
            continue
        candidate = dataset_path / s
        if (candidate / "images").is_dir() and (candidate / "labels").is_dir():
            return candidate / "images", candidate / "labels", yaml_path

    raise ValueError(
        f"Could not find valid 'images/' and 'labels/' directories in {dataset_path} "
        f"(checked subdirectories: {splits_to_check})"
    )


def load_ground_truth(
    label_path: Path, width: int, height: int, vocabulary: Sequence[str]
) -> list[GroundTruth]:
    if not label_path.exists():
        raise ValueError(f"Missing label file for image: {label_path.name}")
    truths: list[GroundTruth] = []
    for line_number, line in enumerate(label_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(
                f"{label_path}:{line_number}: expected class_id x_center y_center width height"
            )
        class_id, x_center, y_center, box_width, box_height = fields
        class_index = int(class_id)
        if not 0 <= class_index < len(vocabulary):
            raise ValueError(
                f"{label_path}:{line_number}: invalid class id {class_index} for vocabulary of size {len(vocabulary)}"
            )
        values = [float(x_center), float(y_center), float(box_width), float(box_height)]
        if any(value < 0 or value > 1 for value in values):
            raise ValueError(
                f"{label_path}:{line_number}: YOLO coordinates must be normalized to [0, 1]"
            )
        box_width_px = values[2] * width
        box_height_px = values[3] * height
        truths.append(
            GroundTruth(
                class_name=vocabulary[class_index],
                box=BoundingBox(
                    x=values[0] * width - box_width_px / 2,
                    y=values[1] * height - box_height_px / 2,
                    width=box_width_px,
                    height=box_height_px,
                ),
            )
        )
    return truths


def run_evaluation(
    dataset_path: Path,
    iou_threshold: float = 0.50,
    split: str | None = None,
    data_yaml_path: Path | None = None,
    class_agnostic: bool = False,
) -> dict:
    image_dir, label_dir, discovered_yaml = resolve_dataset_directories(dataset_path, split)
    yaml_file = data_yaml_path or discovered_yaml

    model_vocab = DatasetVocabulary.coco()
    dataset_vocab = DatasetVocabulary.from_yaml(yaml_file) if yaml_file else model_vocab

    is_compatible = model_vocab.is_compatible_with(dataset_vocab)

    if not is_compatible and not class_agnostic:
        mismatch_msg = dataset_vocab.describe_mismatch(model_vocab)
        raise VocabularyMismatchError(
            f"{mismatch_msg}\n\n"
            f"To test detector box localization capabilities without claiming SKU accuracy, "
            f"run with --class-agnostic."
        )

    service = VisionService()
    samples: list[tuple[list, list]] = []

    for image_path in sorted(image_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        width, height = service.processor.image_dimensions(image_path)
        predictions = service.analyze(str(image_path)).detections
        truths = load_ground_truth(
            label_dir / f"{image_path.stem}.txt",
            width,
            height,
            dataset_vocab.names,
        )
        samples.append((predictions, truths))

    if not samples:
        raise ValueError(f"No supported images found in {image_dir}")

    metrics = evaluate_dataset(
        samples, iou_threshold=iou_threshold, class_agnostic=class_agnostic
    )

    report = {
        "model": "YOLOX-S",
        "model_version": "0.1.1rc0",
        "model_vocabulary": "COCO (80 classes)",
        "dataset_vocabulary_size": dataset_vocab.nc,
        "evaluation_mode": "class_agnostic_localization" if class_agnostic else "direct_class_match",
        "sku_classification_valid": is_compatible and not class_agnostic,
        "iou_threshold": iou_threshold,
        **metrics.__dict__,
    }

    if not is_compatible and class_agnostic:
        report["vocabulary_mismatch_notice"] = (
            "Model is pretrained on COCO (80 classes) while dataset has 62 retail SKU classes. "
            "Metrics reflect spatial localization/objectness recall only, not SKU recognition accuracy."
        )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the local detector against YOLO-format benchmark datasets with vocabulary validation."
    )
    parser.add_argument("dataset", type=Path, help="Dataset directory or benchmark split")
    parser.add_argument("--split", type=str, default=None, help="Dataset split (e.g. test, valid, train)")
    parser.add_argument("--data-yaml", type=Path, default=None, help="Explicit path to data.yaml")
    parser.add_argument("--iou", type=float, default=0.50, help="IoU threshold for matching (default: 0.50)")
    parser.add_argument(
        "--class-agnostic",
        action="store_true",
        help="Run class-agnostic localization evaluation (box IoU matching only)",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    if not 0 < args.iou <= 1:
        print("Error: --iou must be greater than 0 and at most 1", file=sys.stderr)
        sys.exit(1)

    try:
        report = run_evaluation(
            dataset_path=args.dataset,
            iou_threshold=args.iou,
            split=args.split,
            data_yaml_path=args.data_yaml,
            class_agnostic=args.class_agnostic,
        )
    except VocabularyMismatchError as e:
        error_report = {
            "status": "incompatible_vocabulary",
            "error": str(e),
            "model_vocabulary": "COCO (80 classes)",
            "action_required": "Fine-tune or train detector on this SKU dataset before running direct SKU evaluation.",
        }
        print(json.dumps(error_report, indent=2), file=sys.stderr)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(error_report, indent=2) + "\n")
        sys.exit(2)
    except Exception as e:
        print(f"Evaluation Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
