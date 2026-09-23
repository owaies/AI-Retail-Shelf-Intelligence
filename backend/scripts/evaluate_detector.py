from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.evaluation import (
    DatasetVocabulary,
    GroundTruth,
    VocabularyMismatchError,
    evaluate_dataset,
)
from app.services.vision import BoundingBox, DetectionResult, VisionService

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def find_data_yaml(target_path: Path) -> Path | None:
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
    yaml_path = find_data_yaml(dataset_path)

    if (dataset_path / "images").is_dir() and (dataset_path / "labels").is_dir():
        return dataset_path / "images", dataset_path / "labels", yaml_path

    splits_to_check = [split] if split else ["test", "valid", "val", "train"]
    for split_name in splits_to_check:
        if not split_name:
            continue
        candidate = dataset_path / split_name
        if (candidate / "images").is_dir() and (candidate / "labels").is_dir():
            return candidate / "images", candidate / "labels", yaml_path

    raise ValueError(
        f"Could not find valid 'images/' and 'labels/' directories in {dataset_path} "
        f"(checked subdirectories: {splits_to_check})"
    )


def parse_yolo_label_line(
    line: str, width: int = 1, height: int = 1
) -> tuple[float, float, float, float, int] | None:
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


def load_ground_truth(
    label_path: Path, width: int, height: int, vocabulary: Sequence[str]
) -> list[GroundTruth]:
    if not label_path.exists():
        raise ValueError(f"Missing label file for image: {label_path.name}")

    truths: list[GroundTruth] = []
    for line_number, line in enumerate(label_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        parsed = parse_yolo_label_line(line, width, height)
        if parsed is None:
            raise ValueError(
                f"{label_path}:{line_number}: expected YOLO box or polygon format"
            )
        x1, y1, x2, y2, class_index = parsed
        if not 0 <= class_index < len(vocabulary):
            raise ValueError(
                f"{label_path}:{line_number}: invalid class id {class_index} "
                f"for vocabulary of size {len(vocabulary)}"
            )
        truths.append(
            GroundTruth(
                class_name=vocabulary[class_index],
                box=BoundingBox(
                    x=x1,
                    y=y1,
                    width=max(0.0, x2 - x1),
                    height=max(0.0, y2 - y1),
                ),
            )
        )
    return truths


def run_evaluation(
    dataset_path: Path,
    iou_threshold: float = 0.50,
    split: str | None = None,
    data_yaml_path: Path | None = None,
    model_path: Path | None = None,
    model_vocab_path: Path | None = None,
    class_agnostic: bool = False,
) -> dict:
    image_dir, label_dir, discovered_yaml = resolve_dataset_directories(dataset_path, split)
    yaml_file = data_yaml_path or discovered_yaml
    if not yaml_file:
        raise ValueError("A data.yaml is required for class-aware retail evaluation")

    dataset_vocab = DatasetVocabulary.from_yaml(yaml_file)
    model_vocab = (
        DatasetVocabulary.from_yaml(model_vocab_path)
        if model_vocab_path
        else DatasetVocabulary.coco()
    )
    is_compatible = model_vocab.is_compatible_with(dataset_vocab)

    if not is_compatible and not class_agnostic:
        mismatch_msg = dataset_vocab.describe_mismatch(model_vocab)
        raise VocabularyMismatchError(
            f"{mismatch_msg}\n\n"
            "For a trained retail detector, pass --model-path and --model-vocab-yaml. "
            "For the old COCO baseline, use --class-agnostic only as a localization diagnostic."
        )

    if not model_path:
        raise ValueError(
            "Evaluation requires an explicit local --model-path. "
            "This prevents benchmark runs from downloading model weights implicitly."
        )

    detector = VisionService(
        model_path=model_path,
        class_names=model_vocab.names,
        model_name="YOLOX-S",
        model_version="retail-62" if model_path else "0.1.1rc0",
        allow_model_download=False,
    )

    image_paths = [p for p in sorted(image_dir.iterdir()) if p.suffix.lower() in IMAGE_EXTENSIONS]
    if not image_paths:
        raise ValueError(f"No supported images found in {image_dir}")

    total_images = len(image_paths)
    samples: list[tuple[list[DetectionResult], list[GroundTruth]]] = []
    for idx, image_path in enumerate(image_paths, start=1):
        width, height = detector.processor.image_dimensions(image_path)
        predictions = detector.analyze(str(image_path)).detections
        truths = load_ground_truth(
            label_dir / f"{image_path.stem}.txt",
            width,
            height,
            dataset_vocab.names,
        )
        samples.append((predictions, truths))
        if idx % 500 == 0 or idx == total_images:
            print(f"Evaluated [{idx}/{total_images}] images...", file=sys.stderr, flush=True)

    metrics = evaluate_dataset(
        samples, iou_threshold=iou_threshold, class_agnostic=class_agnostic
    )

    return {
        "model": "YOLOX-S",
        "model_version": "retail-62" if model_path else "0.1.1rc0",
        "model_vocabulary_size": model_vocab.nc,
        "dataset_vocabulary_size": dataset_vocab.nc,
        "evaluation_mode": "class_agnostic_localization" if class_agnostic else "class_aware",
        "sku_classification_valid": is_compatible and not class_agnostic,
        "iou_threshold": iou_threshold,
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "mAP50": metrics.ap50,
        "mAP50_95": metrics.map50_95,
        "images": metrics.images,
        "ground_truths": metrics.ground_truths,
        "predictions": metrics.predictions,
        "true_positives": metrics.true_positives,
        "false_positives": metrics.false_positives,
        "false_negatives": metrics.false_negatives,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a YOLOX detector against a YOLO-format retail benchmark."
    )
    parser.add_argument("dataset", type=Path, help="Dataset directory or benchmark split")
    parser.add_argument("--split", type=str, default=None, help="Dataset split (e.g. test, valid)")
    parser.add_argument("--data-yaml", type=Path, default=None, help="Explicit dataset data.yaml")
    parser.add_argument("--model-path", type=Path, required=True, help="Local ONNX detector to evaluate; no implicit downloads")
    parser.add_argument(
        "--model-vocab-yaml",
        type=Path,
        default=None,
        help="data.yaml describing the class vocabulary emitted by --model-path",
    )
    parser.add_argument("--iou", type=float, default=0.50, help="IoU threshold for precision/recall")
    parser.add_argument(
        "--class-agnostic",
        action="store_true",
        help="Evaluate localization without requiring class equality; not SKU accuracy.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    if not 0 < args.iou <= 1:
        print("Error: --iou must be greater than 0 and at most 1", file=sys.stderr)
        sys.exit(1)

    if args.model_path and not args.model_vocab_yaml:
        print("Error: --model-vocab-yaml is required with --model-path", file=sys.stderr)
        sys.exit(1)

    try:
        report = run_evaluation(
            dataset_path=args.dataset,
            iou_threshold=args.iou,
            split=args.split,
            data_yaml_path=args.data_yaml,
            model_path=args.model_path,
            model_vocab_path=args.model_vocab_yaml,
            class_agnostic=args.class_agnostic,
        )
    except VocabularyMismatchError as exc:
        error_report = {
            "status": "incompatible_vocabulary",
            "error": str(exc),
            "action_required": "Use the trained retail ONNX model and matching data.yaml for SKU evaluation.",
        }
        print(json.dumps(error_report, indent=2), file=sys.stderr)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(error_report, indent=2) + "\n")
        sys.exit(2)
    except Exception as exc:
        print(f"Evaluation Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
