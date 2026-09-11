# AI Retail Shelf Intelligence

AI-powered shelf image analysis that turns uploaded images into structured visual observations: detected objects, counts, confidence scores, bounding boxes, persisted analysis records, and evidence-bounded telemetry.

> **GitHub Portfolio Project #2** · One repository for the complete project.

## Live Application

**Frontend:** https://ai-retail-shelf-intelligence.vercel.app/

**Backend:** https://ai-retail-shelf-intelligence-backen.vercel.app/

**Health:** https://ai-retail-shelf-intelligence-backen.vercel.app/api/health

Production deployment is on Vercel using the repository's `main` branch.

## Current Status

**Day 4.5 · Vision quality upgrade in progress**

The full-stack application, authenticated workflow, persistence, history, analytics, CSV export, and production deployment are implemented. The current work is improving the generic detector baseline before claiming retail-specific accuracy.

## Problem

Retail teams can collect large numbers of shelf photographs, but raw images are difficult to search, compare, and summarize. A useful prototype should turn each image into structured computer-vision evidence while avoiding unsupported claims about inventory or out-of-stock state.

## Solution

The application provides an authenticated workspace where a user can upload a shelf image, run OpenCV preprocessing and YOLOX inference, review bounding-box detections, persist the result in PostgreSQL/Supabase, browse historical analyses, inspect individual records, export telemetry as CSV, and review aggregate class-level analytics.

The detector is currently a general-purpose COCO model. Therefore, the application deliberately reports **observable object categories**, not SKU identity or stock status.

## Features

### Analysis workflow

- Authenticated login using Supabase Auth
- JPEG, PNG and WebP validation
- 10 MB upload limit
- Magic-byte and OpenCV decode validation
- Secure temporary-file processing
- OpenCV letterbox preprocessing at 416×416
- YOLOX-S ONNX Runtime inference
- Bounding boxes, class names and confidence scores
- Per-class counts and object coverage
- Evidence-bounded shelf assessment
- Persistent analysis and detection records

### History intelligence

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

### Analytics

- Total stored analyses
- Total detections
- Average detections per scan
- Model/version telemetry
- Aggregated class distribution
- Top detected classes visualization
- CSV export of class distribution
- Explicit evidence boundary preventing unsupported stock claims

### Vision quality upgrade

The original YOLOX-Tiny baseline was replaced with the higher-capacity official **YOLOX-S** checkpoint and a recall-oriented 0.20 confidence threshold. This is an engineering baseline improvement, not a measured accuracy claim. Precision, recall and mAP must be evaluated on a representative labeled retail test set before reporting model performance.

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite | Fast, typed single-page application |
| Styling | CSS | Responsive product UI without unnecessary dependency weight |
| Routing | React Router | Protected application pages and detail URLs |
| Backend | Python + FastAPI | Typed REST API and clean service boundary |
| Computer Vision | OpenCV | Image decoding and YOLOX-compatible preprocessing |
| Object Detection | YOLOX-S 0.1.1rc0 | Higher-capacity general-purpose detector baseline |
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
                    │    YOLOX-S / ONNX        │
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

## Model Strategy

**YOLOX-S 0.1.1rc0** is executed locally through ONNX Runtime.

- Input: 416×416
- Runtime: ONNX Runtime CPU
- Pretrained labels: COCO
- Model source: Megvii YOLOX
- License: Apache-2.0
- Confidence threshold: 0.20
- NMS IoU threshold: 0.45

The model is downloaded on demand from the official release and is not committed to the repository.

### Important limitation

COCO labels are generic object categories. A `bottle` detection does not identify a particular retail SKU, brand, facing count, or inventory state. The UI therefore labels stock-state inference as **not claimed** rather than presenting an unsupported prediction.

### Accuracy work

The screenshot-driven review exposed missed and semantically incorrect detections on shelf-like imagery. That is expected from a generic COCO detector and is now treated as a model-quality problem rather than a UI problem.

The next evaluation must use a representative labeled retail dataset and report actual:

- Precision
- Recall
- mAP@50
- mAP@50:95
- Per-class metrics
- False positives and missed detections

No accuracy number is claimed until that evaluation is completed.

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
