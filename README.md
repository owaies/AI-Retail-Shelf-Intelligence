# AI Retail Shelf Intelligence

AI-powered shelf image analysis for retailers to turn shelf photos into structured visual intelligence such as detected objects, product counts, confidence scores and shelf-area observations.

> **Project #2** in the GitHub portfolio. This repository is the single repository for the complete project.

## Current Status

**Day 1 · Foundation implemented and verified through CI**

The application shell, FastAPI boundary, vision-service interfaces, image-validation foundation, database migration, environment strategy and CI are in place. Computer-vision inference and persistent analysis APIs are intentionally **not** marked complete yet.

## Problem

Retail shelf checks are often manual and inconsistent. Repeated images can contain useful evidence about visible products, shelf coverage and potential stock issues, but that evidence is difficult to inspect and compare without a structured workflow.

## Solution

Retail Vision Intelligence is being built as a full-stack computer-vision workspace:

```text
Shelf image
   ↓
Validation
   ↓
OpenCV preprocessing
   ↓
Local YOLO inference
   ↓
Detection results
   ↓
Shelf analysis
   ↓
PostgreSQL / Supabase
   ↓
History + analytics + visual evidence
```

## Implemented on Day 1

- React + TypeScript + Vite application shell
- Responsive navigation and planned workspace routes
- Futuristic / Sci-Fi + Dashboard / Data-Heavy visual system
- Typed frontend API service boundary
- FastAPI application with `GET /api/health`
- Environment-variable configuration strategy
- Image metadata validation utilities for JPEG, PNG and WebP
- 10 MB image-size ceiling in the validation foundation
- `VisionService` and `ImageProcessor` boundaries for Day 2 integration
- PostgreSQL migration for users, analyses, detections and shelf regions
- Basic pytest health test
- GitHub Actions for backend tests and frontend production build
- Architecture documentation
- Secret-safe `.gitignore` and `.env.example`

## Planned / Not Yet Implemented

- Actual image upload endpoint
- Temporary-file decoding and OpenCV preprocessing
- Local YOLO inference
- Real detection results and bounding boxes
- Shelf-region inference and low-stock/empty-area classification
- Analysis persistence APIs
- Supabase Storage integration
- Authentication/authorization
- History queries and analytics
- Production deployment

These are deliberately separated from the Day 1 implementation so the repository never presents mock computer-vision output as real AI behavior.

## Technology Stack

| Layer | Technology | Day 1 role |
|---|---|---|
| Frontend | React + TypeScript + Vite | Application shell and routes |
| Styling | CSS design tokens | Futuristic responsive UI system |
| Backend | Python + FastAPI | REST API boundary |
| Validation | Pydantic Settings | Environment configuration |
| Vision | OpenCV + YOLO | Planned local inference pipeline |
| Database | PostgreSQL / Supabase | Planned relational persistence |
| Testing | pytest + FastAPI TestClient | Backend foundation test |
| CI | GitHub Actions | Backend test + frontend build |

### Why these technologies?

- **React** provides a component model for an image-analysis dashboard.
- **TypeScript** makes API contracts and detection data explicit.
- **Vite** provides a fast, straightforward frontend build system.
- **FastAPI** gives the Python vision stack a typed, lightweight HTTP boundary.
- **PostgreSQL** fits relational analysis history, detections and ownership relationships.
- **Supabase** is the planned managed PostgreSQL/storage layer while staying within the free-tier requirement.
- **OpenCV** is appropriate for image decoding and preprocessing before inference.
- **Local YOLO-family inference** avoids a paid inference API. The Day 2 model choice will be validated for license and runtime suitability before integration.

## Model Strategy

No model is invoked in Day 1.

The current candidate for Day 2 is **YOLOX-tiny**, an open-source YOLO-family detector released under the Apache-2.0 license, with local inference and publicly available pretrained weights. The model will only be adopted after its runtime, weight source and suitability for retail imagery are verified. A general COCO detector should not be presented as SKU-level retail recognition without appropriate data/model support.

No paid inference service is planned.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the Day 1 boundary and target analysis pipeline.

## Database Design

The initial migration is at [`backend/migrations/001_initial_schema.sql`](backend/migrations/001_initial_schema.sql).

```text
users
  │
  └──< analyses
          │
          ├──< detections
          └──< shelf_regions
```

`analyses.user_id` establishes ownership. Foreign keys cascade analysis-owned child records when an analysis is deleted. Confidence and geometric fields have database constraints.

Direct Supabase Auth/RLS integration is **not** claimed in Day 1 because the authentication architecture has not yet been implemented.

## Frontend Routes

| Route | Purpose | Day 1 status |
|---|---|---|
| `/` | Dashboard | Foundation shell |
| `/analyze` | Shelf analysis | Upload-ready empty state |
| `/history` | Analysis history | Empty state |
| `/analytics` | Retail telemetry | Empty state |
| `/settings` | Configuration | Foundation information |

## API

Implemented:

```http
GET /api/health
```

Response:

```json
{"status":"ok","service":"retail-vision-api"}
```

Future analysis endpoints will only be added when their underlying persistence/inference behavior exists.

## Local Development

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

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

### Tests

```bash
cd backend
pytest
```

## Environment Variables

Copy `.env.example` to `.env` and provide only the values required by the stage you are implementing.

Current Day 1 frontend configuration:

```text
VITE_API_BASE_URL=/api
```

Backend database configuration is reserved for the persistence stage:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

Never commit real credentials, database passwords, JWT secrets or Supabase service-role keys.

## Security Foundation

- Uploaded filenames are treated as untrusted metadata.
- Allowed image MIME types and extensions are explicitly constrained.
- Image size is capped before future processing.
- The future CV pipeline is designed around controlled temporary files rather than user-provided filesystem paths.
- Secrets are environment-only and ignored by Git.
- No authentication bypass or mock detection path exists.

Authentication, authorization, CORS hardening and database access policies will be implemented and verified when those capabilities are introduced.

## CI

GitHub Actions runs:

1. Python 3.12 dependency installation and `pytest` in `backend/`.
2. Node 22 dependency installation and `npm run build` in `frontend/`.

The Day 1 commit should only be considered verified after the repository's CI reports the jobs as successful.

## Development Plan

### Day 1 · Foundation

Architecture, UI system, frontend shell, FastAPI boundary, vision interfaces, image-validation foundation, database migration, environment strategy, tests, CI and documentation.

### Day 2 · Backend + Database + Vision

Image upload, OpenCV preprocessing, validated temporary-file handling, YOLO integration, detection schemas, persistence and real analysis endpoints.

### Day 3 · Frontend + Integration

Real upload flow, analysis API integration, image/detection visualization, history and responsive result states.

### Day 4 · Intelligence + UX

Shelf-region analysis, low-stock/empty-area reasoning, analytics, search/filtering, storage and UX/security refinement.

### Day 5 · Testing + Polish + Deployment

End-to-end verification, edge cases, production configuration and deployment if a suitable free-tier architecture is technically viable.

## Cost Policy

Strictly free/no-cost development. No paid plans, billing upgrades, paid APIs, paid AI APIs or paid inference services will be enabled without explicit approval.

## License

Project licensing will be finalized alongside the production dependency/model review.

## Author

**MOHAMMED OWAIES**  
GitHub: https://github.com/owaies
