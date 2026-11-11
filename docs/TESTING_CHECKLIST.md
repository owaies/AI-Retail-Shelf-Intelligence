# Analysis testing checklist

Use this checklist when changing the shelf-analysis workflow.

## Input validation
- Test supported JPEG, PNG, and WebP uploads using valid encoded image files.
- Test oversized compressed files.
- Test images whose decoded dimensions exceed 40 megapixels, even when the compressed upload is small.
- Test invalid or corrupted image data and mismatched filename, MIME type, and actual image format.
- Confirm rejected uploads do not create analysis records.
- Override `MAX_UPLOAD_BYTES` and confirm the analysis endpoint enforces the configured byte limit.
- Confirm startup rejects non-positive model, upload, or request-body limits.
- Confirm `MAX_REQUEST_BODY_BYTES` is not smaller than `MAX_UPLOAD_BYTES`.

## Detection
- Confirm bounding boxes remain inside image dimensions.
- Verify confidence values and class counts are consistent.
- Check empty-detection results explicitly.

## Persistence
- Confirm authenticated users can see only their own analysis history.
- Verify deletion removes the intended analysis and its dependent detections.
- Check CSV export matches the active history filters.

## UI
- Verify loading, error, and empty states.
- Check analysis details on narrow and wide viewports.
