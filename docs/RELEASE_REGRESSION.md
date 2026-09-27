# Retail release regression plan

Run these checks after detector, API, or history changes.

## Upload
Test valid and invalid image types, oversized files, corrupted payloads, and filenames containing unusual characters.

## Analysis
Verify detections, counts, confidence values, dimensions, model version, and empty-result behavior.

## History
Test search, filters, detail views, deletion, and CSV export while authenticated as separate users.

## Production
Verify the frontend can reach the deployed backend without weakening authentication or CORS boundaries.
