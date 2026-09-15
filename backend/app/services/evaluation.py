from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import yaml

from app.services.vision import BoundingBox, COCO_CLASSES, DetectionResult


class VocabularyMismatchError(ValueError):
    """Raised when evaluation is attempted between incompatible class vocabularies."""
    pass


@dataclass(frozen=True)
class DatasetVocabulary:
    """Represents the set and ordering of class names for a dataset or model."""
    names: tuple[str, ...]

    @property
    def nc(self) -> int:
        return len(self.names)

    @classmethod
    def coco(cls) -> DatasetVocabulary:
        return cls(names=COCO_CLASSES)

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> DatasetVocabulary:
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Vocabulary YAML file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML format in {path}: expected a dictionary mapping")
        names_entry = data.get("names")
        if isinstance(names_entry, list):
            names = tuple(str(n) for n in names_entry)
        elif isinstance(names_entry, dict):
            # Formats like {0: 'classA', 1: 'classB'}
            sorted_indices = sorted(int(k) for k in names_entry.keys())
            names = tuple(str(names_entry[i]) for i in sorted_indices)
        else:
            raise ValueError(f"YAML at {path} missing valid 'names' list or dict")
        expected_nc = data.get("nc")
        if expected_nc is not None and int(expected_nc) != len(names):
            raise ValueError(
                f"YAML at {path} declares nc={expected_nc} but defines {len(names)} class names"
            )
        return cls(names=names)

    def is_compatible_with(self, other: DatasetVocabulary | Sequence[str]) -> bool:
        other_names = other.names if isinstance(other, DatasetVocabulary) else tuple(other)
        return self.names == other_names

    def describe_mismatch(self, other: DatasetVocabulary | Sequence[str]) -> str:
        other_names = other.names if isinstance(other, DatasetVocabulary) else tuple(other)
        return (
            f"Class vocabulary mismatch:\n"
            f"  Expected ({len(self.names)} classes): {list(self.names[:5])}{'...' if len(self.names) > 5 else ''}\n"
            f"  Provided ({len(other_names)} classes): {list(other_names[:5])}{'...' if len(other_names) > 5 else ''}\n"
            f"Direct SKU evaluation with an incompatible class vocabulary is invalid."
        )


@dataclass(frozen=True)
class GroundTruth:
    class_name: str
    box: BoundingBox


@dataclass(frozen=True)
class EvaluationMetrics:
    images: int
    ground_truths: int
    predictions: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    ap50: float


def iou(a: BoundingBox, b: BoundingBox) -> float:
    ax2, ay2 = a.x + a.width, a.y + a.height
    bx2, by2 = b.x + b.width, b.y + b.height
    ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = a.width * a.height + b.width * b.height - intersection
    return intersection / union if union > 0 else 0.0


def _average_precision(recalls: list[float], precisions: list[float]) -> float:
    if not recalls:
        return 0.0
    envelope = precisions[:]
    for index in range(len(envelope) - 2, -1, -1):
        envelope[index] = max(envelope[index], envelope[index + 1])
    points = [0.0, *recalls, 1.0]
    values = [envelope[0], *envelope, envelope[-1]]
    return sum((points[i + 1] - points[i]) * values[i + 1] for i in range(len(points) - 1))


def evaluate_image(
    predictions: list[DetectionResult],
    ground_truths: list[GroundTruth],
    iou_threshold: float = 0.5,
    class_agnostic: bool = False,
) -> tuple[int, int, int]:
    """Return TP, FP, FN using confidence-ranked greedy one-to-one matching."""
    matched: set[int] = set()
    true_positives = 0
    for prediction in sorted(predictions, key=lambda item: item.confidence, reverse=True):
        candidates = [
            (index, iou(prediction.box, truth.box))
            for index, truth in enumerate(ground_truths)
            if index not in matched and (class_agnostic or truth.class_name == prediction.class_name)
        ]
        if candidates:
            best_index, best_iou = max(candidates, key=lambda item: item[1])
            if best_iou >= iou_threshold:
                matched.add(best_index)
                true_positives += 1
    return true_positives, len(predictions) - true_positives, len(ground_truths) - true_positives


def evaluate_dataset(
    samples: list[tuple[list[DetectionResult], list[GroundTruth]]],
    iou_threshold: float = 0.5,
    class_agnostic: bool = False,
) -> EvaluationMetrics:
    """Evaluate a labeled dataset at one IoU threshold.

    When class_agnostic is True, bounding boxes are matched based purely on IoU
    overlap to measure localization/objectness recall without requiring class equality.
    When class_agnostic is False, boxes only match if class_name is identical.
    """
    true_positives = false_positives = false_negatives = 0
    ranked: list[tuple[float, bool]] = []
    total_ground_truths = 0
    for predictions, ground_truths in samples:
        matched: set[int] = set()
        for prediction in sorted(predictions, key=lambda item: item.confidence, reverse=True):
            candidates = [
                (index, iou(prediction.box, truth.box))
                for index, truth in enumerate(ground_truths)
                if index not in matched and (class_agnostic or truth.class_name == prediction.class_name)
            ]
            is_match = bool(candidates) and max(candidates, key=lambda item: item[1])[1] >= iou_threshold
            if is_match:
                best_index = max(candidates, key=lambda item: item[1])[0]
                matched.add(best_index)
                true_positives += 1
            else:
                false_positives += 1
            ranked.append((prediction.confidence, is_match))
        false_negatives += len(ground_truths) - len(matched)
        total_ground_truths += len(ground_truths)

    precision = true_positives / (true_positives + false_positives) if true_positives + false_positives else 0.0
    recall = true_positives / total_ground_truths if total_ground_truths else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    ranked.sort(key=lambda item: item[0], reverse=True)
    tp = fp = 0
    recalls: list[float] = []
    precisions: list[float] = []
    for _, matched_prediction in ranked:
        if matched_prediction:
            tp += 1
        else:
            fp += 1
        recalls.append(tp / total_ground_truths if total_ground_truths else 0.0)
        precisions.append(tp / (tp + fp) if tp + fp else 0.0)

    return EvaluationMetrics(
        images=len(samples),
        ground_truths=total_ground_truths,
        predictions=len(ranked),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1=f1,
        ap50=_average_precision(recalls, precisions),
    )
