# AI Retail Shelf Intelligence

AI-powered shelf image analysis that turns uploaded images into structured visual observations: detected objects, counts, confidence scores, bounding boxes, persisted analysis records, and evidence-bounded telemetry.

> **GitHub Portfolio Project #2** · One repository for the complete project.

## Live Application

**Frontend:** https://ai-retail-shelf-intelligence.vercel.app/

**Backend:** https://ai-retail-shelf-intelligence-backen.vercel.app/

**Health:** https://ai-retail-shelf-intelligence-backen.vercel.app/api/health

Production deployment is on Vercel using the repository's `main` branch. The latest production deployment was verified as `READY`, and the frontend production URL returned HTTP 200.

## Current Status

**Day 5 · Testing + Polish + Deployment**

The project has completed the planned Day 1–4 implementation and production integration. The authenticated workflow has been manually exercised through the deployed UI, including analysis creation, persisted history, analytics, CSV export, detail inspection, and deletion confirmation.

## Problem

Retail teams can collect large numbers of shelf photographs, but raw images are difficult to search, compare, and summarize. A useful prototype should turn each image into structured computer-vision evidence while avoiding unsupported claims about inventory or out-of-stock state.

## Solution

The application provides an authenticated workspace where a user can upload a shelf image, run OpenCV preprocessing and YOLOX-Tiny inference, review bounding-box detections, persist the result in PostgreSQL/Supabase, browse historical analyses, inspect individual records, export telemetry as CSV, and review aggregate class-level analytics.

The current detector is a general-purpose COCO model. Therefore, the application deliberately reports **observable object categories**, not SKU identity or stock status.

## Features

### Analysis workflow

- Authenticated login using Supabase Auth
- JPEG, PNG and WebP validation
- 10 MB upload limit
- Magic-byte and OpenCV decode validation
- Secure temporary-file processing
- OpenCV letterbox preprocessing at 416×416
- YOLOX-Tiny ONNX Runtime inference
- Bounding boxes, class names and confidence scores
- Per-class counts and object coverage
- Evidence-bounded shelf assessment
- Persistent analysis and detection records

### Day 4 History intelligence

- Search analysis history by filename
- Filter by model
- Sort by newest, oldest, or detection count
- Responsive history table
- Open a persisted analysis detail view
- Detection-level coordinates and confidence inspection
- Model/version and image metadata
- Authenticated deletion with confirmation
- CSV export of filtered history
- Empty, loading and request-error states

### Day 4 Analytics

- Total stored analyses
- Total detections
- Average detections per scan
- Model/version telemetry
- Aggregated class distribution
- Top detected classes visualization
- CSV export of class distribution
- Explicit evidence boundary preventing unsupported stock claims

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite | Fast, typed single-page application |
| Styling | CSS | Responsive product UI without unnecessary dependency weight |
| Routing | React Router | Protected application pages and detail URLs |
| Backend | Python + FastAPI | Typed REST API and clean service boundary |
| Computer Vision | OpenCV | Image decoding and YOLOX-compatible preprocessing |
| Object Detection | YOLOX-Tiny 0.1.1rc0 | Lightweight general-purpose detector |
| Inference | ONNX Runtime | Local CPU inference without a paid inference API |
| Database | PostgreSQL via Supabase | Relational persistence for users, analyses and detections |
| Authentication | Supabase Auth + bearer JWT | Authenticated frontend sessions and API authorization |
| CI | GitHub Actions | Backend tests, CV smoke test, API startup check and frontend build |
| Deployment | Vercel | Free-tier-friendly production hosting |

## Architecture

```text
                    ┌──────────────────────────┐
                    │      React + Vite         │
                    │  Login / Analyze /        │
                    │  History / Analytics      │
                    └────────────┬─────────────┘
                                 │
                       Bearer JWT + multipart
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │        FastAPI            │
                    │ /api/analyses             │
                    │ auth + validation         │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │          OpenCV            │
                    │ decode + letterbox 416²  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   YOLOX-Tiny / ONNX      │
                    │ boxes + classes + scores │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Shelf Analyzer       │
                    │ counts + object coverage │
                    │ evidence-bounded output  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ PostgreSQL / Supabase     │
                    │ users → analyses          │
                    │ analyses → detections     │
                    │          → shelf_regions  │
                    └──────────────────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the backend request lifecycle and model boundaries.

## Data Model

```text
users
  │
  └──< analyses
          │
          ├──< detections
          └──< shelf_regions
```

Each analysis belongs to an authenticated user. API reads and deletes are scoped by both analysis ID and authenticated user ID. Child records are related through foreign keys.

## Supabase

The project uses the existing Supabase project configured for this application. Production authentication and persisted analysis records have been verified through the deployed application.

Schema:

```text
retail_shelf_intelligence
```

Tables:

- `users`
- `analyses`
- `detections`
- `shelf_regions`

No service-role key is exposed in the frontend. Client configuration uses the Supabase URL and publishable key, while server-only database/auth configuration remains in deployment environment variables.

## Model Strategy

**YOLOX-Tiny 0.1.1rc0** is executed locally through ONNX Runtime.

- Input: 416×416
- Runtime: ONNX Runtime CPU
- Pretrained labels: COCO
- Model source: Megvii YOLOX
- License: Apache-2.0

Official references:

- https://github.com/Megvii-BaseDetection/YOLOX
- https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE
- https://github.com/Megvii-BaseDetection/YOLOX/blob/main/demo/ONNXRuntime/README.md

The model is downloaded on demand from the pinned official release and is not committed to the repository.

### Important limitation

COCO labels are generic object categories. A `bottle` detection does not identify a particular retail SKU, brand, facing count, or inventory state. The UI therefore labels stock-state inference as **not claimed** rather than presenting an unsupported prediction.

## API

### Health

```http
GET /api/health
```

### Create analysis

```http
POST /api/analyses
Authorization: Bearer <access-token>
Content-Type: multipart/form-data
```

### List analyses

```http
GET /api/analyses
Authorization: Bearer <access-token>
```

### Get analysis

```http
GET /api/analyses/{analysis_id}
Authorization: Bearer <access-token>
```

### Delete analysis

```http
DELETE /api/analyses/{analysis_id}
Authorization: Bearer <access-token>
```

## Security

- Allowed upload types: JPEG, PNG and WebP
- Maximum upload size: 10 MB
- MIME type, extension, magic bytes and OpenCV decode are validated
- Client filenames are metadata only and never treated as filesystem paths
- Temporary files are cleaned after processing
- JWT validation requires the expected user claims and issuer/expiry checks
- Analysis queries are scoped to the authenticated user
- No API keys, database passwords or service-role credentials are committed
- No paid inference API is required

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Tests:

```bash
pytest
```

The CV integration test can run the pinned YOLOX model/sample with `RUN_CV_INTEGRATION=1`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
npm run build
```

## Environment Variables

Copy `.env.example` to `.env` for local development and provide real values only through local/deployment environment configuration.

Frontend:

```text
VITE_API_BASE_URL=<backend API URL>
VITE_SUPABASE_URL=<Supabase project URL>
VITE_SUPABASE_PUBLISHABLE_KEY=<Supabase publishable key>
```

Backend configuration includes the PostgreSQL connection and JWT/model settings. Never commit those real values.

## CI / Verification

GitHub Actions runs on pushes and pull requests to `main` and verifies:

1. Python 3.12 dependency installation
2. Backend pytest suite
3. Pinned YOLOX CV integration path
4. FastAPI startup and `/api/health` smoke check
5. Node 22 dependency installation
6. Frontend production build

The CI run for commit `5ea3fe7649dd1196a740d05a89cb009b6c829ec3` completed successfully.

Production verification completed for the current deployment:

- Vercel deployment state: `READY`
- Frontend production response: HTTP 200
- Backend production health: HTTP 200
- Backend production runtime error scan: no error/fatal logs in the checked two-hour window
- Authenticated application flow: manually exercised
- History CSV export: manually verified
- Analytics class distribution and CSV export: manually verified
- Delete confirmation flow: manually verified

## Day-by-Day Progress

### Day 1 · Foundation

Architecture, repository structure, frontend shell, FastAPI boundary, CV interfaces, database design, environment strategy and CI foundation.

### Day 2 · Backend + Database + Vision

Secure upload validation, OpenCV preprocessing, YOLOX-Tiny ONNX inference, detection contracts, analysis APIs, PostgreSQL persistence, JWT verification foundation and CV integration testing.

### Day 3 · Frontend + Integration

Real authenticated frontend-to-API workflow, upload analysis, OpenCV/YOLO pipeline states, result visualization, bounding boxes, persistence, History and Analytics integration.

### Day 4 · Intelligence + UX

History search/filter/sort, persisted detail inspection, deletion, CSV export, aggregate detection analytics, responsive UX refinements and explicit evidence boundaries.

### Day 5 · Testing + Polish + Deployment

CI verification, production Vercel deployment, backend health/runtime verification, production frontend verification and authenticated end-to-end UI evidence.

## Future Scope

- Fine-tune a shelf-specific detector for retail SKUs
- Add validated shelf-region segmentation
- Introduce calibrated stock/availability estimation only after suitable labeled data
- Add pagination/server-side aggregation for larger datasets
- Add role-based retail/team workspaces
- Add richer comparison and trend analytics
- Add object-level visual audit overlays and exportable reports

## Cost Policy

The project is designed around free-tier tooling: GitHub, Supabase and Vercel. No paid domain, paid hosting plan or paid AI inference API is required.

## Author

**MOHAMMED OWAIES**  
GitHub: https://github.com/owaies
