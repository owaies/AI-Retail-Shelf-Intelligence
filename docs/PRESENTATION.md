# AI Retail Shelf Intelligence

## Presentation Deck Source

This Markdown deck is the repository-safe source for the project presentation. It is intentionally evidence-bound to the current implementation and does not claim SKU-level accuracy that has not been measured.

---

## Slide 1 — Title

**AI Retail Shelf Intelligence**

Computer-vision shelf analysis for retail operations.

- React + Vite frontend
- FastAPI backend
- YOLOX-S inference
- Production deployment on Vercel

---

## Slide 2 — Problem

Retail teams need a faster way to inspect shelf images and turn visual evidence into structured analysis.

Manual inspection is:

- slow at scale
- difficult to standardize
- disconnected from historical analysis
- dependent on human availability

The product focuses on turning shelf imagery into a repeatable analysis workflow.

---

## Slide 3 — Solution

The application accepts a shelf image, runs computer-vision inference, and presents structured results through a web interface.

Core flow:

`Upload → API → YOLOX-S → detections → shelf analysis → dashboard`

The system keeps detection evidence separate from unsupported business claims such as exact stock state.

---

## Slide 4 — Architecture

### Frontend

- React
- Vite
- TypeScript
- Responsive retail dashboard

### Backend

- FastAPI
- Pydantic settings
- SQLAlchemy persistence
- OpenCV image processing

### Vision

- YOLOX-S
- ONNX Runtime
- 640 × 640 inference
- confidence threshold: 0.20
- NMS IoU: 0.45

---

## Slide 5 — Vision Pipeline

1. Receive uploaded shelf image.
2. Validate image dimensions and payload.
3. Preprocess with the configured image processor.
4. Run YOLOX-S inference.
5. Decode detections.
6. Apply confidence/NMS filtering.
7. Convert detections into shelf-analysis records.
8. Persist analysis metadata and return structured results.

---

## Slide 6 — Product Features

- Shelf image analysis
- Detection visualization
- Analysis history
- Retail dashboard
- Object coverage measurement
- Authentication and protected analysis data
- Responsive frontend
- Production API health endpoint

---

## Slide 7 — Security & Data Boundaries

The application uses authenticated user context for protected analysis workflows.

Important boundary:

**Detection is not automatically inventory truth.**

The current system can measure visual object coverage, but it does not claim that every detection proves:

- exact stock quantity
- SKU identity
- out-of-stock state
- planogram compliance

Those require validated retail-specific data and evaluation.

---

## Slide 8 — Evaluation Reality

The repository contains a reproducible retail evaluation protocol and records the current detector limitation.

The short fine-tuning experiment did not produce a production-ready retail detector at the configured threshold.

Therefore production continues to use the stable YOLOX-S baseline rather than presenting unsupported SKU-level metrics.

This is an intentional engineering decision: measured limitations are documented instead of hidden.

---

## Slide 9 — Testing & CI

Regression coverage includes:

- detector configuration contract
- offline model-loading behavior
- shelf-analysis calculations
- invalid image handling
- evaluation/compile verification
- backend pytest suite
- frontend production build

The latest verified production commit has successful Vercel frontend and backend checks.

---

## Slide 10 — Deployment

Production services:

- Frontend: Vercel
- Backend: Vercel
- Source: GitHub

Current verified commit:

`5c50bf1eeb9c1263dfad8a4b7993d8a27e8281ed`

The corresponding Vercel frontend and backend status checks are successful.

---

## Slide 11 — Engineering Decisions

### Why YOLOX-S?

It provides a practical production baseline while keeping inference lightweight enough for a serverless-oriented deployment.

### Why ONNX Runtime?

It provides a portable inference path without requiring a full training stack in production.

### Why keep retail fine-tuning separate?

A detector should not be promoted into production until its retail-specific evaluation supports the intended claim.

---

## Slide 12 — Future Work

The highest-value next improvement is a properly trained and evaluated retail detector.

Target workflow:

`collect retail images → annotate SKUs → train locally → validate → benchmark → compare against YOLOX-S → promote only if metrics improve`

This experiment should remain local/free unless an explicitly free compute tier is available and suitable.

---

## Slide 13 — Interview Summary

**One-line explanation:**

> I built a full-stack computer-vision application that analyzes retail shelf images with YOLOX-S, exposes inference through FastAPI, persists analysis history, and presents the results in a React dashboard, while explicitly separating measured visual evidence from unsupported inventory claims.

**Strongest engineering point:**

The project documents and tests its production safety boundary instead of treating model detections as automatic inventory truth.

---

## Slide 14 — Closing

**AI Retail Shelf Intelligence**

From shelf image to structured visual intelligence.

Repository:
https://github.com/owaies/AI-Retail-Shelf-Intelligence
