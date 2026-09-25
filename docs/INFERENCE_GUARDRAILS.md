# Shelf inference guardrails

The current detector is a general-purpose model. The application should distinguish observable detections from retail conclusions.

## Allowed evidence
Report detected object categories, counts, confidence scores, bounding boxes, and model/version information.

## Avoid unsupported claims
Do not infer SKU identity, exact inventory levels, or out-of-stock status unless a validated retail-specific model and evidence pipeline supports those claims.

## Regression
Keep a fixed test image set and compare detection behavior after changes to preprocessing, confidence thresholds, or model versions.
