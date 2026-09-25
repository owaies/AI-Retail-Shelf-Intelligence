# Model limitations

The current shelf analysis uses a pretrained YOLOX model with generic COCO categories.

## Implications

A detected bottle or similar object does not by itself identify a specific SKU, brand, facing count, or inventory state.

## Product guidance

Treat generic detections as visual evidence rather than authoritative inventory facts. A future custom retail dataset can improve SKU-level recognition and shelf-specific metrics.

## Validation

Model changes should be evaluated against a representative set of shelf images containing different lighting, occlusion, product density, and camera angles.
