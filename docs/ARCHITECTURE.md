# Architecture

## Day 1 boundary

```text
Browser
  │
  ▼
React + TypeScript + Vite
  │  typed API service
  ▼
FastAPI REST API
  │
  ├── API routes
  ├── image validation
  └── vision-service boundary
          │
          ├── OpenCV preprocessing (Day 2)
          └── YOLO inference (Day 2)
  │
  ▼
PostgreSQL / Supabase
  ├── users
  ├── analyses
  ├── detections
  └── shelf_regions
```

## Responsibilities

### Frontend
- Owns navigation, responsive presentation and user interaction.
- Uses a typed API service instead of scattering HTTP calls through components.
- Does not perform computer-vision inference.

### FastAPI
- Provides the HTTP boundary.
- Validates server-side inputs.
- Owns future analysis orchestration and authorization boundaries.

### Vision layer
`ImageProcessor` and `VisionService` are intentionally interfaces at this stage. Day 1 does not invoke a model or return fabricated detections.

### Data layer
The initial PostgreSQL migration establishes user ownership, analysis records, detections and shelf-region observations. Application persistence will be wired in the backend/database day.

## Analysis pipeline target

```text
Upload
  ↓
Metadata + byte validation
  ↓
Safe temporary file
  ↓
OpenCV preprocessing
  ↓
Local YOLO inference
  ↓
DetectionResult[]
  ↓
Shelf-region analysis
  ↓
Persist analysis + detections
  ↓
Typed API response
  ↓
Frontend visualization
```

## Deployment direction

No production deployment is performed on Day 1. The frontend is designed for a Vercel-compatible build, while the vision-capable FastAPI service will need a technically suitable free-tier runtime before production deployment is selected.
