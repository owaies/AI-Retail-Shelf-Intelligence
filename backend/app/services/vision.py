from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class DetectionResult:
    class_name: str
    confidence: float
    box: BoundingBox


class VisionService:
    """Stable interface for local CV inference.

    Day 1 deliberately contains no model invocation and produces no mock detections.
    Day 2 can provide a YOLO-backed implementation without changing the API boundary.
    """

    def analyze(self, image_path: str) -> list[DetectionResult]:
        raise NotImplementedError("Vision inference is scheduled for Day 2.")
