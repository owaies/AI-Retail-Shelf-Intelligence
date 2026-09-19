from pathlib import Path
import pytest

from app.services.evaluation import (
    DatasetVocabulary,
    GroundTruth,
    VocabularyMismatchError,
    evaluate_dataset,
    iou,
)
from app.services.vision import BoundingBox, DetectionResult
from scripts.evaluate_detector import (
    load_ground_truth,
    run_evaluation,
)


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
    assert metrics.map50_95 == 1.0


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
    assert metrics.map50_95 == 0.0


def test_class_agnostic_evaluation_matches_overlapping_boxes_regardless_of_class():
    samples = [
        (
            [prediction("cup", confidence=0.95)],
            [GroundTruth("bottle", box())],
        )
    ]
    metrics = evaluate_dataset(samples, class_agnostic=True)
    assert metrics.true_positives == 1
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0
    assert metrics.ap50 == 1.0
    assert metrics.map50_95 == 1.0


def test_map_is_averaged_over_present_classes():
    samples = [
        (
            [prediction("bottle", confidence=0.95), prediction("cup", confidence=0.9)],
            [GroundTruth("bottle", box()), GroundTruth("cup", box())],
        )
    ]
    metrics = evaluate_dataset(samples)
    assert metrics.ap50 == pytest.approx(1.0)
    assert metrics.map50_95 == pytest.approx(1.0)


def test_dataset_vocabulary_from_yaml_list(tmp_path: Path):
    yaml_file = tmp_path / "data.yaml"
    yaml_file.write_text("nc: 3\nnames: ['cola', 'chips', 'water']\n")
    vocab = DatasetVocabulary.from_yaml(yaml_file)
    assert vocab.nc == 3
    assert vocab.names == ("cola", "chips", "water")


def test_dataset_vocabulary_from_yaml_dict(tmp_path: Path):
    yaml_file = tmp_path / "data.yaml"
    yaml_file.write_text("nc: 2\nnames:\n  0: cola\n  1: water\n")
    vocab = DatasetVocabulary.from_yaml(yaml_file)
    assert vocab.nc == 2
    assert vocab.names == ("cola", "water")


def test_dataset_vocabulary_nc_mismatch_raises(tmp_path: Path):
    yaml_file = tmp_path / "data.yaml"
    yaml_file.write_text("nc: 5\nnames: ['cola', 'water']\n")
    with pytest.raises(ValueError, match="declares nc=5 but defines 2"):
        DatasetVocabulary.from_yaml(yaml_file)


def test_vocabulary_compatibility_detection():
    coco_vocab = DatasetVocabulary.coco()
    custom_vocab = DatasetVocabulary(names=("BargsBlack20Oz", "BuenoShareSize"))

    assert coco_vocab.is_compatible_with(DatasetVocabulary.coco()) is True
    assert coco_vocab.is_compatible_with(custom_vocab) is False
    mismatch_desc = coco_vocab.describe_mismatch(custom_vocab)
    assert "Expected (80 classes)" in mismatch_desc
    assert "Provided (2 classes)" in mismatch_desc


def test_load_ground_truth_with_valid_and_invalid_classes(tmp_path: Path):
    label_file = tmp_path / "sample.txt"
    label_file.write_text("0 0.5 0.5 0.2 0.4\n1 0.3 0.3 0.1 0.1\n")
    vocab = ("item_a", "item_b")

    truths = load_ground_truth(label_file, width=100, height=200, vocabulary=vocab)
    assert len(truths) == 2
    assert truths[0].class_name == "item_a"
    assert truths[1].class_name == "item_b"

    label_file_bad = tmp_path / "bad.txt"
    label_file_bad.write_text("99 0.5 0.5 0.2 0.4\n")
    with pytest.raises(ValueError, match="invalid class id 99"):
        load_ground_truth(label_file_bad, width=100, height=200, vocabulary=vocab)


def test_run_evaluation_rejects_sku_vocabulary_mismatch_without_silent_coco_conversion(tmp_path: Path):
    dataset_dir = tmp_path / "retail"
    images_dir = dataset_dir / "images"
    labels_dir = dataset_dir / "labels"
    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    yaml_file = dataset_dir / "data.yaml"
    yaml_file.write_text("nc: 2\nnames: ['BargsBlack20Oz', 'BuenoShareSize']\n")

    img_file = images_dir / "shelf.jpg"
    import numpy as np
    import cv2
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(img_file), dummy_img)

    lbl_file = labels_dir / "shelf.txt"
    lbl_file.write_text("0 0.5 0.5 0.2 0.2\n")

    with pytest.raises(VocabularyMismatchError, match="Class vocabulary mismatch"):
        run_evaluation(dataset_dir)
