# Analysis testing checklist

Use this checklist when changing the shelf-analysis workflow.

## Input validation
- Test supported JPEG, PNG, and WebP uploads.
- Test oversized files.
- Test invalid or corrupted image data.
- Confirm rejected uploads do not create analysis records.

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
