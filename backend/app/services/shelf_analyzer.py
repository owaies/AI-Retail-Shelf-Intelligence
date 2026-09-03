from __future__ import annotations

from dataclasses import dataclass

from app.services.vision import DetectionResult


@dataclass(frozen=True)
class ShelfAssessment:
    status: str
    object_coverage: float
    low_stock_supported: bool
    note: str


class ShelfAnalyzer:
    """Evidence-bounded shelf analysis.

    YOLOX-Tiny is pretrained on COCO, not shelf/SKU data, so this stage does not
    infer stock levels or empty shelf positions. It reports only observable object
    coverage and explicitly marks stock assessment as unknown.
    """

    def assess(self, detections: list[DetectionResult], width: int, height: int) -> ShelfAssessment:
        if width <= 0 or height <= 0:
            return ShelfAssessment("unknown", 0.0, False, "Image dimensions are invalid")
        coverage = 0.0
        # Sum is intentionally capped. Exact union coverage is computed by VisionService;
        # this fallback keeps the service independently testable.
        for detection in detections:
            coverage += max(0.0, detection.box.width) * max(0.0, detection.box.height)
        coverage = min(1.0, coverage / (width * height))
        return ShelfAssessment(
            status="unknown",
            object_coverage=coverage,
            low_stock_supported=False,
            note="Stock-level and empty-shelf inference is deferred until a shelf-specific model or validated shelf-region detector is available.",
        )
