from __future__ import annotations

import os
import tempfile
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings
from app.services.image_processor import ImageProcessor, PreparedImage

COCO_CLASSES = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich",
    "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush",
)

RETAIL_RELEVANT_CLASSES = {
    "bottle", "wine glass", "cup", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "book", "toothbrush",
}

MODEL_NAME = "YOLOX-Tiny"
MODEL_VERSION = "0.1.1rc0"


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


@dataclass(frozen=True)
class VisionAnalysis:
    width: int
    height: int
    detections: list[DetectionResult]
    class_counts: dict[str, int]
    retail_relevant_counts: dict[str, int]
    object_coverage: float


class VisionService:
    """Local YOLOX ONNX inference. No paid inference service and no mock results."""

    def __init__(self, processor: ImageProcessor | None = None) -> None:
        self.processor = processor or ImageProcessor(settings.model_input_size)
        self._session = None

    def _model_path(self) -> Path:
        path = Path(settings.model_path)
        if path.exists() and path.stat().st_size > 0:
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, dir=path.parent, suffix=".onnx") as tmp:
            temporary = Path(tmp.name)
        try:
            with urllib.request.urlopen(settings.model_url, timeout=60) as response, temporary.open("wb") as output:
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > settings.max_model_bytes:
                        raise RuntimeError("YOLO model exceeds the configured size limit")
                    output.write(chunk)
            temporary.replace(path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return path

    def _session_or_create(self):
        if self._session is None:
            import onnxruntime as ort
            self._session = ort.InferenceSession(str(self._model_path()), providers=["CPUExecutionProvider"])
        return self._session

    @staticmethod
    def _nms(boxes: np.ndarray, scores: np.ndarray, threshold: float) -> list[int]:
        if len(boxes) == 0:
            return []
        x1, y1, x2, y2 = boxes.T
        areas = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        order = scores.argsort()[::-1]
        keep: list[int] = []
        while order.size:
            i = int(order[0])
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            union = areas[i] + areas[order[1:]] - inter
            iou = np.divide(inter, union, out=np.zeros_like(inter), where=union > 0)
            order = order[1:][iou <= threshold]
        return keep

    @staticmethod
    def _postprocess(output: np.ndarray, prepared: PreparedImage, confidence: float, nms_threshold: float) -> list[DetectionResult]:
        predictions = output[0] if output.ndim == 3 else output
        h, w = prepared.input_size
        grids, strides = [], []
        for stride in (8, 16, 32):
            hs, ws = h // stride, w // stride
            xv, yv = np.meshgrid(np.arange(ws), np.arange(hs))
            grids.append(np.stack((xv, yv), axis=2).reshape(1, -1, 2))
            strides.append(np.full((1, hs * ws, 1), stride, dtype=np.float32))
        grid = np.concatenate(grids, axis=1)
        expanded = np.concatenate(strides, axis=1)
        predictions = predictions.copy()
        predictions[:, :2] = (predictions[:, :2] + grid[0]) * expanded[0]
        predictions[:, 2:4] = np.exp(np.clip(predictions[:, 2:4], -20, 20)) * expanded[0]

        boxes = np.empty_like(predictions[:, :4])
        boxes[:, 0] = predictions[:, 0] - predictions[:, 2] / 2
        boxes[:, 1] = predictions[:, 1] - predictions[:, 3] / 2
        boxes[:, 2] = predictions[:, 0] + predictions[:, 2] / 2
        boxes[:, 3] = predictions[:, 1] + predictions[:, 3] / 2
        boxes /= prepared.ratio
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, prepared.width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, prepared.height)

        objectness = predictions[:, 4:5]
        class_probs = predictions[:, 5:]
        class_ids = class_probs.argmax(axis=1)
        scores = objectness[:, 0] * class_probs[np.arange(len(predictions)), class_ids]
        candidates = np.flatnonzero(scores >= confidence)
        results: list[DetectionResult] = []
        for class_id in np.unique(class_ids[candidates]) if len(candidates) else []:
            cls_candidates = candidates[class_ids[candidates] == class_id]
            keep = VisionService._nms(boxes[cls_candidates], scores[cls_candidates], nms_threshold)
            for index in keep:
                box = boxes[cls_candidates[index]]
                results.append(DetectionResult(
                    class_name=COCO_CLASSES[int(class_id)],
                    confidence=float(scores[cls_candidates[index]]),
                    box=BoundingBox(float(box[0]), float(box[1]), float(box[2] - box[0]), float(box[3] - box[1])),
                ))
        return sorted(results, key=lambda item: item.confidence, reverse=True)

    def analyze(self, image_path: str) -> VisionAnalysis:
        prepared = self.processor.prepare(Path(image_path))
        session = self._session_or_create()
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: prepared.tensor[None, ...]})[0]
        detections = self._postprocess(output, prepared, settings.detection_confidence, settings.nms_iou_threshold)
        counts = Counter(item.class_name for item in detections)
        retail_counts = {name: count for name, count in counts.items() if name in RETAIL_RELEVANT_CLASSES}
        union_mask = np.zeros((prepared.height, prepared.width), dtype=np.uint8)
        for item in detections:
            x1, y1 = int(item.box.x), int(item.box.y)
            x2, y2 = int(item.box.x + item.box.width), int(item.box.y + item.box.height)
            cv2.rectangle(union_mask, (x1, y1), (x2, y2), 1, -1)
        coverage = float(union_mask.mean()) if union_mask.size else 0.0
        return VisionAnalysis(prepared.width, prepared.height, detections, dict(counts), retail_counts, coverage)
