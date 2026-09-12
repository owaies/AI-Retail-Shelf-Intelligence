from app.services.evaluation import GroundTruth, evaluate_dataset, iou
from app.services.vision import BoundingBox, DetectionResult


def box(x=0, y=0, width=10, height=10):
    return BoundingBox(x, y, width, height)


def prediction(name="bottle", confidence=0.9, shape=None):
    return DetectionResult(name, confidence, shape or box())


def test_iou_is_one_for_identical_boxes():
    assert iou(box(), box()) == 1.0


def test_dataset_metrics_match_one_to_one_predictions():
    samples = [
        (
            [prediction(), prediction(confidence=0.4)],
            [GroundTruth("bottle", box())],
        )
    ]
    metrics = evaluate_dataset(samples)
    assert metrics.images == 1
    assert metrics.ground_truths == 1
    assert metrics.predictions == 2
    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 0
    assert metrics.precision == 0.5
    assert metrics.recall == 1.0
    assert metrics.f1 == 2 / 3
    assert metrics.ap50 == 1.0


def test_wrong_class_is_false_positive_and_missed_ground_truth():
    metrics = evaluate_dataset(
        [([prediction("cup")], [GroundTruth("bottle", box())])]
    )
    assert metrics.true_positives == 0
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0
    assert metrics.ap50 == 0.0
