# AI Retail Shelf Intelligence

AI-powered shelf image analysis for retailers to detect visible products, count items, and identify potentially empty or low-stock shelf areas.

> **Project #2** in the GitHub portfolio. This repository is the single repository for the complete project.

## Project Status

**Day 1 · Foundation**

The repository is currently being established. Implementation details will be updated as features are genuinely built and verified.

## Problem

Local retailers often inspect shelves manually. This makes it difficult to consistently identify missing products, low-stock areas, and shelf-level inventory patterns from repeated store checks.

## Planned Solution

A full-stack computer-vision application that accepts shelf images, processes them through a Python/FastAPI vision pipeline, stores analysis records, and presents detection results and historical analytics in a React dashboard.

## Planned Core Features

- Shelf image upload
- Product/object detection with YOLO where suitable
- OpenCV preprocessing
- Bounding-box visualization
- Visible product counting
- Potential empty/low-stock shelf-area detection
- Detection history
- Search and filtering
- Analytics dashboard
- Uploaded image/result storage
- User-scoped analysis records
- Exportable analysis reports where appropriate

Only features that are actually implemented and verified will be marked as complete.

## Planned Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Styling | Project-specific responsive UI system |
| Backend | Python + FastAPI |
| Computer Vision | YOLO + OpenCV, where appropriate |
| Database | PostgreSQL / Supabase |
| Storage | Supabase Storage, where appropriate |
| Authentication | JWT/Auth, where appropriate |
| Deployment | Vercel for suitable frontend workloads; free-tier compatible backend deployment strategy |
| Containerization | Docker where useful for the vision service |

Technologies will be retained only where they solve an actual project requirement.

## Planned Architecture

```text
User
  ↓
React + TypeScript Dashboard
  ↓
FastAPI REST API
  ↓
Image Validation / Preprocessing
  ↓
YOLO + OpenCV Vision Pipeline
  ↓
Detection + Shelf Analysis
  ↓
PostgreSQL / Supabase
  ↓
History + Analytics + Results
```

## UI Direction

Unlike Project #1 (JobTrack), this project will use a **different primary visual design direction** selected specifically for a computer-vision retail intelligence product. The final direction will be documented before the main UI implementation begins.

## Development Plan

### Day 1 · Foundation
- Define requirements and MVP
- Establish architecture
- Select and document the visual design system
- Create project structure
- Define environment-variable strategy
- Define database plan
- Establish API boundaries
- Add development documentation

### Day 2 · Vision + Backend + Database
- FastAPI foundation
- Image validation/upload pipeline
- OpenCV preprocessing
- YOLO inference integration where appropriate
- Detection response schema
- PostgreSQL/Supabase schema
- Validation and error handling

### Day 3 · Frontend + Integration
- React dashboard
- Image upload experience
- Detection visualization
- API integration
- Loading/error/empty states
- Responsive layouts

### Day 4 · Intelligence + UX
- Detection history
- Search/filter
- Analytics
- Shelf/area analysis
- Storage integration
- Security and performance improvements

### Day 5 · Testing + Deployment + Documentation
- Automated tests
- End-to-end verification
- Production deployment where technically suitable
- README completion
- Screenshots
- Professional PPT
- Interview Cheat Sheet

## Cost Policy

This project is developed using free-tier services and open-source tooling where possible.

No paid plans, billing upgrades, paid APIs, or paid AI APIs will be enabled without explicit approval.

## Security

Secrets must remain in environment variables and must never be committed to GitHub. Production credentials, database passwords, JWT secrets, and service-role keys must not be exposed in source code or logs.

## License

License will be added when the project structure is finalized.
