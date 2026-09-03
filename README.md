# AI Retail Shelf Intelligence

AI-powered shelf image analysis for retailers to turn shelf photos into structured visual intelligence such as detected objects, counts, confidence scores and evidence-bounded shelf observations.

> **Project #2** in the GitHub portfolio. This repository is the single repository for the complete project.

## Current Status

**Day 2 · Backend + Database + Computer Vision integration**

The real FastAPI upload path, secure image validation, OpenCV preprocessing, local YOLOX-Tiny ONNX inference, typed detection results, analysis APIs, PostgreSQL persistence layer, JWT verification foundation and CI CV smoke test are implemented. Supabase is **not claimed as connected** because no dedicated project/database credentials have been configured for this repository.

## What is implemented

- Secure JPEG/PNG/WebP upload validation with a 10 MB limit
- Filename treated as metadata, never as a filesystem path
- Magic-byte validation plus OpenCV decode validation
- Temporary-file processing with automatic cleanup
- OpenCV letterbox preprocessing compatible with YOLOX input expectations
- Local **YOLOX-Tiny 0.1.1rc0** ONNX Runtime inference
- Bounding boxes, class labels and confidence scores
- Per-class detection counts and object-coverage measurement
- REST analysis create/list/detail/delete endpoints
- PostgreSQL repository layer using environment-provided `DATABASE_URL`
- Idempotent migration 002 for CV metadata and object coverage
- JWT bearer-token verification with issuer/expiry requirements
- User ownership enforced in analysis queries
- Evidence-bounded shelf assessment that does **not** invent stock levels
- Backend tests for upload validation, API auth and OpenCV preprocessing
- Real CV integration test against the pinned YOLOX repository sample image
- GitHub Actions backend tests + FastAPI startup smoke check + frontend build

## What is deliberately not claimed

- SKU-level product recognition
- Brand recognition
- Shelf-specific object detection accuracy
- Empty-shelf or low-stock classification
- Supabase connectivity
- Supabase Storage
- Production authentication issuer configuration
- Production deployment

The selected pretrained YOLOX model is trained for the COCO object categories. It can detect generic categories such as bottles, cups, bowls and food items, but that is not equivalent to recognizing individual retail SKUs. Stock-state inference is therefore marked **unknown** until a shelf-specific model/region method is validated.

## Architecture

```text
Client
  │
  │ multipart/form-data
  ▼
FastAPI /api/analyses
  │
  ├── JWT verification
  ├── upload validation
  ├── secure temporary file
  ▼
OpenCV ImageProcessor
  │
  │ letterbox 416×416
  ▼
YOLOX-Tiny ONNX Runtime
  │
  ├── boxes
  ├── classes
  └── confidences
  ▼
ShelfAnalyzer
  │
  └── evidence-bounded object coverage
  ▼
PostgreSQL repository
  │
  ├── users
  ├── analyses
  ├── detections
  └── shelf_regions
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Model strategy

### Selected model

**YOLOX-Tiny 0.1.1rc0**, executed locally through ONNX Runtime.

The official YOLOX documentation lists YOLOX-Tiny at 416×416, 5.06M parameters, 6.45 GFLOPs and 32.8 mAP on its benchmark table. The official ONNX Runtime documentation provides a pre-generated `yolox_tiny.onnx` release asset and shows the corresponding inference flow. YOLOX source is released under **Apache License 2.0**.

Sources:

- https://github.com/Megvii-BaseDetection/YOLOX
- https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE
- https://github.com/Megvii-BaseDetection/YOLOX/blob/main/demo/ONNXRuntime/README.md

The model is downloaded on demand from the pinned official GitHub release URL and is not committed to this repository.

### Retail suitability limitation

YOLOX-Tiny's pretrained detector uses COCO classes, not retail SKU labels. The application therefore exposes **detected object categories** rather than pretending that a generic `bottle` detection is a particular brand or product. A future shelf-specific model can replace the detector behind the same service boundary.

## Database

Migration files:

- `backend/migrations/001_initial_schema.sql`
- `backend/migrations/002_analysis_cv_metadata.sql`

Relationships:

```text
users
  │
  └──< analyses
          │
          ├──< detections
          └──< shelf_regions
```

`analyses.user_id` owns each analysis. Retrieval and deletion are filtered by the authenticated user ID. Foreign keys cascade child records when an owned analysis is deleted.

### Supabase status

**Not connected/verified for this project.** The repository supports PostgreSQL/Supabase-compatible PostgreSQL through `DATABASE_URL`, but no credentials are stored and no new Supabase project was created during Day 2.

Apply migrations only after configuring a real database connection:

```bash
cd backend
python scripts/apply_migrations.py
```

## API

### Health

```http
GET /api/health
```

### Create analysis

```http
POST /api/analyses
Authorization: Bearer <trusted-jwt>
Content-Type: multipart/form-data
```

Form field:

```text
file=<shelf image>
```

### List analyses

```http
GET /api/analyses
Authorization: Bearer <trusted-jwt>
```

### Get one analysis

```http
GET /api/analyses/{analysis_id}
Authorization: Bearer <trusted-jwt>
```

### Delete one analysis

```http
DELETE /api/analyses/{analysis_id}
Authorization: Bearer <trusted-jwt>
```

Analysis endpoints return `401` without authentication and `503` when the required database configuration is absent.

## Security

- Allowed MIME types: JPEG, PNG and WebP
- Allowed extensions: `.jpg`, `.jpeg`, `.png`, `.webp`
- Maximum upload: 10 MB
- File signatures are checked against the declared MIME type
- OpenCV must successfully decode the uploaded content
- Uploaded filenames are never used as storage paths
- Temporary files are generated by the operating system and deleted after processing
- JWT requires `sub`, `exp` and `iss`
- JWT issuer and secret are environment-configured
- Database queries always scope analysis access to the authenticated user ID
- No API keys, database credentials or service-role keys are committed
- No paid inference API is used

## Local development

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

Tests:

```bash
pytest
```

The real model integration test downloads the pinned YOLOX sample/model when `RUN_CV_INTEGRATION=1`.

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

## Environment variables

Copy `.env.example` to `.env` and supply real values only in the local/host environment.

Required for persistent analysis APIs:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

Required for authenticated API access:

```text
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ISSUER=retail-shelf-intelligence
JWT_ALGORITHM=HS256
```

CV configuration:

```text
MODEL_URL=https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_tiny.onnx
MODEL_PATH=.cache/models/yolox_tiny.onnx
MODEL_INPUT_SIZE=416
DETECTION_CONFIDENCE=0.25
NMS_IOU_THRESHOLD=0.45
```

## CI

GitHub Actions verifies:

1. Python 3.12 dependency installation
2. Backend pytest suite
3. Real YOLOX inference against the pinned official YOLOX sample when CI runs with the integration flag
4. FastAPI startup and `/api/health`
5. Node 22 dependency installation
6. Frontend production build

## Day plan

### Day 1 · Foundation

Completed: architecture, frontend shell, FastAPI boundary, CV interfaces, database schema, environment strategy, documentation and CI.

### Day 2 · Backend + Database + Vision

Completed: secure upload validation, OpenCV preprocessing, YOLOX ONNX inference, detection contracts, analysis APIs, PostgreSQL persistence layer, JWT verification foundation and real CI inference test.

### Day 3 · Frontend + Integration

Planned: connect the existing frontend to the real analysis API, upload workflow, analysis result visualization, bounding-box overlays, detection summaries, history and responsive result states.

### Day 4 · Intelligence + UX

Planned: validated shelf-region reasoning, stock/empty-area intelligence where supported by suitable visual evidence, analytics, storage and UX/security refinement.

### Day 5 · Testing + Polish + Deployment

Planned only if needed: end-to-end verification, edge cases, production configuration and free-tier deployment.

## Cost policy

Strictly free/no-cost development. No paid plans, billing upgrades, paid APIs, paid AI APIs or paid inference services are enabled.

## Author

**MOHAMMED OWAIES**  
GitHub: https://github.com/owaies
