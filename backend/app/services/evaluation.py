from __future__ import annotations

from dataclasses import dataclass

from app.services.vision import BoundingBox, DetectionResult


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
) -> tuple[int, int, int]:
    """Return TP, FP, FN using confidence-ranked greedy one-to-one matching."""
    matched: set[int] = set()
    true_positives = 0
    for prediction in sorted(predictions, key=lambda item: item.confidence, reverse=True):
        candidates = [
            (index, iou(prediction.box, truth.box))
            for index, truth in enumerate(ground_truths)
            if index not in matched and truth.class_name == prediction.class_name
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
) -> EvaluationMetrics:
    """Evaluate a labeled dataset at one IoU threshold.

    AP50 is computed globally by ranking all predictions by confidence and
    greedily matching them to the highest-IoU unmatched ground truth of the
    same class in each image.
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
                if index not in matched and truth.class_name == prediction.class_name
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
