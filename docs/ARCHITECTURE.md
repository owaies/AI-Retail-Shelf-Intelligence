# Architecture

## Day 2 backend boundary

```text
React frontend
     │
     │ multipart/form-data + Bearer JWT
     ▼
FastAPI
     │
     ├── authentication / ownership
     ├── upload validation
     └── analysis orchestration
              │
              ▼
        OpenCV ImageProcessor
              │
              │ 416×416 letterbox
              ▼
        YOLOX-Tiny ONNX Runtime
              │
              ├── bounding boxes
              ├── COCO class labels
              └── confidence scores
              │
              ▼
          ShelfAnalyzer
              │
              └── evidence-bounded object coverage
              │
              ▼
       PostgreSQL repository
```

## Request lifecycle

1. FastAPI receives a multipart image and bearer token.
2. JWT signature, expiry, issuer and required user claims are verified.
3. Upload MIME type, extension, size and magic bytes are validated.
4. The file is written to an operating-system temporary file. The client filename is metadata only.
5. OpenCV decodes and letterboxes the image to 416×416.
6. ONNX Runtime executes the pinned YOLOX-Tiny model locally on CPU.
7. YOLOX outputs are decoded using the model's 8/16/32 stride grid, class confidence and per-class NMS.
8. Coordinates are mapped back to the original image dimensions.
9. Detection counts and object coverage are calculated.
10. PostgreSQL persistence stores the owned analysis and its detections in one transaction.
11. The temporary image is removed after inference.

## Model boundary

`VisionService` is intentionally isolated from FastAPI and PostgreSQL. A future shelf-specific detector can replace the YOLOX implementation without changing the API contract.

Current model:

- YOLOX-Tiny
- Release: `0.1.1rc0`
- Input: 416×416
- Runtime: ONNX Runtime CPU
- Pretrained labels: COCO
- Source/license: Megvii YOLOX, Apache-2.0

Because COCO is not a retail SKU dataset, the current system reports generic observable object classes. It does not infer brand/SKU identity or stock state.

## Database boundary

`AnalysisRepository` owns persistence operations. Every read/delete includes both `analysis_id` and the authenticated `user_id`, preventing one user from retrieving another user's analysis through the API layer.

The repository expects PostgreSQL through `DATABASE_URL`. Supabase-compatible PostgreSQL is supported, but no dedicated Supabase connection is configured for this repository yet.

## Shelf intelligence boundary

Day 2 computes **object coverage** only. It does not label an area `empty` or `low_stock` because the selected general-purpose COCO detector does not provide enough shelf-specific evidence for that conclusion.

A future shelf-specific model or validated region detector should populate `shelf_regions` and stock-state fields.
