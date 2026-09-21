from app.services.shelf_analyzer import ShelfAnalyzer
from app.services.vision import BoundingBox, DetectionResult


def test_shelf_analyzer_keeps_stock_state_unclaimed():
    detections = [
        DetectionResult(
            class_name="bottle",
            confidence=0.8,
            box=BoundingBox(x=0, y=0, width=20, height=10),
        )
    ]

    result = ShelfAnalyzer().assess(detections, width=100, height=100)

    assert result.status == "unknown"
    assert result.low_stock_supported is False
    assert result.object_coverage == 0.02
    assert "shelf-specific model" in result.note


def test_shelf_analyzer_caps_fallback_coverage():
    detections = [
        DetectionResult(
            class_name="bottle",
            confidence=0.9,
            box=BoundingBox(x=0, y=0, width=200, height=200),
        )
    ]

    result = ShelfAnalyzer().assess(detections, width=100, height=100)

    assert result.object_coverage == 1.0


def test_shelf_analyzer_rejects_invalid_dimensions():
    result = ShelfAnalyzer().assess([], width=0, height=100)

    assert result.status == "unknown"
    assert result.object_coverage == 0.0
    assert result.low_stock_supported is False
    assert result.note == "Image dimensions are invalid"
