# Retail Inference Data Flow

The computer-vision path separates input validation, image preprocessing, detector execution, and result persistence.

upload -> validation -> temporary file -> preprocessing -> YOLOX inference -> normalized detections -> database history

## Model boundary

The repository uses an ONNX Runtime inference path with a YOLOX-S checkpoint baseline. Model and version information is retained with analysis metadata so later history can identify which detector configuration produced a result.

## Engineering rule

Do not interpret raw detections as inventory truth without representative evaluation. The existing documentation intentionally separates engineering baselines from measured retail performance claims.
