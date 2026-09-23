# Portfolio README Supplement

This document is the verified portfolio-facing status sheet for **AI Retail Shelf Intelligence**. It complements the root `README.md` without replacing its technical documentation.

## Project snapshot

- **Repository:** https://github.com/owaies/AI-Retail-Shelf-Intelligence
- **Frontend:** https://ai-retail-shelf-intelligence.vercel.app/
- **Backend:** https://ai-retail-shelf-intelligence-backen.vercel.app/
- **Health endpoint:** https://ai-retail-shelf-intelligence-backen.vercel.app/api/health
- **Current verified commit:** `a13d1274bd9a9e1da3da92f01aee6b7dade168ac`
- **CI:** GitHub Actions run #111 passed
- **Production deployment status:** both Vercel checks reported success for the verified commit

## What the product does

AI Retail Shelf Intelligence converts an uploaded shelf photograph into structured computer-vision evidence. The application supports authenticated analysis, image validation, OpenCV preprocessing, YOLOX-S ONNX inference, bounding boxes, class counts, confidence scores, persisted analysis history, analytics, CSV export, and authenticated deletion.

## Architecture at a glance

```text
React + Vite
    │
    │ Bearer JWT + multipart image
    ▼
FastAPI
    │
    ├── validation / authorization
    │
    ▼
OpenCV
    │  decode + 640×640 letterbox
    ▼
YOLOX-S / ONNX Runtime
    │  boxes + classes + confidence
    ▼
Shelf Analyzer
    │  counts + coverage + evidence boundary
    ▼
PostgreSQL / Supabase
```

## Verified engineering decisions

### Detection baseline

Production uses the official **YOLOX-S 0.1.1rc0** checkpoint through ONNX Runtime with a 640×640 input, confidence threshold 0.20, and NMS IoU threshold 0.45.

### Evidence boundary

The production detector is a general COCO model. It can report observable categories such as `bottle`, but it does **not** claim SKU identity, brand recognition, facing counts, or inventory/out-of-stock state.

### Retail fine-tuning status

The repository contains a measured retail benchmark for the 3-epoch fine-tuned checkpoint. On the held-out test split, that checkpoint produced zero predictions at confidence ≥ 0.20, yielding measured precision, recall, F1, mAP@50 and mAP@50:95 of zero. This result is retained as a limitation rather than replaced with an unsupported accuracy claim.

A longer 15–30 epoch local GPU training run is the documented next model-quality experiment. No paid cloud GPU or paid inference API is required for the current production baseline.

## Verification status

### Automated CI

The latest GitHub Actions CI run for commit `a13d1274bd9a9e1da3da92f01aee6b7dade168ac` completed successfully. The workflow covers:

- backend dependency installation
- training dependency installation
- backend pytest suite
- API startup / health smoke test
- frontend dependency installation
- frontend production build

### Deployment

The verified commit reports successful Vercel checks for both the frontend and backend deployments.

## Portfolio talking points

1. **Full-stack AI:** React/TypeScript frontend connected to a FastAPI computer-vision backend.
2. **Computer vision:** OpenCV preprocessing plus ONNX Runtime YOLOX-S inference.
3. **Security:** Supabase Auth with bearer JWT authorization and authenticated persistence.
4. **Data engineering:** relational analysis/detection persistence with searchable history and CSV telemetry export.
5. **Responsible AI:** the UI and documentation distinguish observable detections from unsupported inventory claims.
6. **Engineering discipline:** regression tests, CI, deployment checks, benchmark evidence, and explicit model limitations are part of the project rather than hidden behind a demo.

## Remaining work before final completion

- Complete the documented extended local retail fine-tuning experiment if SKU-level detection is required.
- Re-evaluate the fine-tuned model on the held-out test set using reproducible metrics before changing the production detector.
- Produce the portfolio presentation (PPT) from verified repository facts.
- Review and update the interview cheat sheet against the final measured state.
- Perform final repository, CI, deployment, and documentation verification.

No credentials, private keys, or paid services belong in this document.
