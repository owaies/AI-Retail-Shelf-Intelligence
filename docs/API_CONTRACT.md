# Retail Intelligence API Contract

The backend is a FastAPI service with authenticated analysis history, image processing, detector inference, and health endpoints.

## Analysis boundary

The analysis route accepts an image, validates it, writes a temporary processing artifact, runs the configured detector, and persists user-scoped analysis metadata and detections.

Uploads must use a supported extension and matching MIME type: `.jpg`/`.jpeg` with `image/jpeg`, `.png` with `image/png`, or `.webp` with `image/webp`. The server also checks the file signature against the declared MIME type; matching only one of these values is insufficient.

## Stable expectations

Clients should handle loading, empty, validation, authentication, and server-error states independently. Analysis history should remain scoped to the authenticated user, and exported results should correspond to the selected filtered history.

## Change checklist

When adding a request field, update the schema, route, frontend API client and types, and backend tests. Keep large or malformed media rejected before expensive image decoding or inference whenever possible. Upload validation tests should cover extension, MIME type, and file-signature agreement independently.
