# Shelf analysis data lifecycle

The application processes an uploaded shelf image into structured analysis data.

## Processing
1. Validate the upload.
2. Decode and preprocess the image.
3. Run YOLOX inference.
4. Persist the analysis and detection records.
5. Present history, details, analytics, and CSV export.

## User isolation
Authenticated users should only access their own stored analyses.

## Deletion
Deletion flows should confirm the intended record and remove dependent detection data consistently.

## Export
CSV exports should reflect the currently filtered history and remain evidence-bounded.
