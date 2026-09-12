# Detector evaluation workflow

The retail vision baseline is evaluated locally against a labeled image set. The repository does **not** ship a benchmark dataset, so no retail accuracy numbers are claimed until real labels are supplied.

## Dataset layout

```text
benchmark/
├── images/
│   ├── shelf_001.jpg
│   └── shelf_002.jpg
└── labels/
    ├── shelf_001.txt
    └── shelf_002.txt
```

Each label file uses standard YOLO normalized coordinates:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Class IDs follow the COCO class ordering used by `backend/app/services/vision.py`.

## Run the benchmark

From `backend/`:

```bash
python scripts/evaluate_detector.py ../benchmark --output ../benchmark/report.json
```

The evaluator runs the real local YOLOX-S ONNX inference path, converts the YOLO labels into image-space boxes, and reports:

- image count
- ground-truth count
- prediction count
- true positives
- false positives
- false negatives
- precision
- recall
- F1
- AP50

The default matching threshold is IoU 0.50 and can be changed with `--iou`.

## Interpretation boundary

This harness measures the current detector against the supplied labels. It does not manufacture a dataset, and it does not turn COCO-trained classes into SKU-level retail classes. For a meaningful retail benchmark, use a representative labeled shelf dataset and report the resulting measurements unchanged.
