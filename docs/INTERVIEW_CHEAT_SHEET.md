# AI Retail Shelf Intelligence — Interview Cheat Sheet

## 30-second explanation

AI Retail Shelf Intelligence is a full-stack computer-vision application that lets an authenticated user upload shelf images and turn them into structured visual evidence. A React/TypeScript frontend sends the image to a FastAPI backend, which validates it, preprocesses it with OpenCV, runs YOLOX-Tiny through ONNX Runtime, and persists the analysis and detections in PostgreSQL/Supabase. The UI then provides result visualization, searchable history, record details, deletion, analytics, and CSV export. The current model uses generic COCO classes, so the application deliberately does not claim SKU identity or stock status.

## 2-minute explanation

The problem is that shelf photographs contain useful information but are difficult to search and summarize manually. I built a small full-stack system that converts each image into structured computer-vision observations.

The frontend is React with TypeScript and Vite. Supabase Auth handles login, and the frontend keeps the authenticated access token in the browser session and sends it as a bearer token to the API. The backend is FastAPI. Before inference, it validates JPEG/PNG/WebP uploads, checks size, extension, MIME/signature information and OpenCV decodability, then processes the file temporarily.

For vision, OpenCV performs YOLOX-compatible 416×416 letterbox preprocessing. YOLOX-Tiny 0.1.1rc0 runs locally through ONNX Runtime on CPU. The result contains bounding boxes, generic COCO class labels and confidence scores. I map the detections back to the original image dimensions and calculate counts and object coverage.

The persistence layer stores the authenticated user's analyses and child detection records in PostgreSQL through the configured Supabase database. API reads and deletes are scoped to the authenticated user, so a user cannot request another user's analysis simply by changing an ID.

For Day 4, I added history search, model filtering, sorting, persisted detail inspection, CSV export, deletion confirmation, aggregate class analytics and responsive UI states. The analytics page explicitly states that stock status is not claimed because the current COCO detector is not a retail SKU or inventory model.

The application is deployed on Vercel, CI runs through GitHub Actions, and the production frontend/backend health checks were verified.

---

## Technology Q&A

### 1. Why React + TypeScript?

React provides component-based UI and TypeScript catches incorrect data usage at compile time. The application has multiple protected pages and typed API/domain objects, so the combination keeps the frontend manageable.

### 2. Why FastAPI?

FastAPI is a good fit for a Python computer-vision backend because it provides typed request/response handling, clean routing, automatic API documentation and integrates naturally with Python libraries such as OpenCV and ONNX Runtime.

### 3. Why PostgreSQL?

The application has relational data: users own analyses, analyses contain detections, and analyses can have shelf-region records. PostgreSQL handles those relationships and constraints naturally.

### 4. Why Supabase?

Supabase provides PostgreSQL plus authentication and a practical hosted development workflow. In this project the database is PostgreSQL/Supabase-compatible and Supabase Auth is used for login.

### 5. Why Vercel?

The React/Vite frontend is well suited to Vercel's static/SPA deployment model, and the FastAPI backend is deployed separately as its own Vercel project. It also fits the project's free-tier constraint.

### 6. Why YOLOX-Tiny?

It is substantially lighter than larger detectors and is practical for a prototype that needs object detection without a paid inference API. The service boundary also allows it to be replaced later by a shelf-specific model.

### 7. Why ONNX Runtime?

It lets the backend execute the exported detector without depending on a separate paid inference service. The current implementation uses CPU inference.

### 8. Why OpenCV?

OpenCV provides reliable image decoding and the preprocessing needed to transform the input into the model's expected 416×416 letterboxed representation.

---

## Architecture Q&A

### 9. Explain the request flow.

React authenticates the user, selects an image, and sends multipart/form-data plus a bearer token to FastAPI. FastAPI verifies authentication and validates the upload, OpenCV preprocesses it, YOLOX performs inference, the service derives counts/coverage, PostgreSQL stores the result, and the response returns structured analysis data to the frontend.

### 10. Why is the model isolated behind a service boundary?

It prevents the API layer from being tightly coupled to YOLOX. A future retail-specific detector can implement the same vision contract without rewriting the routes or persistence layer.

### 11. How are bounding boxes handled?

The model runs on a 416×416 letterboxed image. After decoding detections, the preprocessing scale and padding are accounted for so coordinates can be mapped back to the original image dimensions.

### 12. What does object coverage mean?

It is a derived measurement of how much image area is covered by detected objects. It is an observation from the detector, not an inventory percentage.

### 13. Why not call a bottle an actual retail product?

Because YOLOX-Tiny is using COCO labels. A generic `bottle` class does not identify a brand, SKU, facing count, or inventory quantity. Claiming that would exceed the available evidence.

### 14. Why is stock status explicitly not claimed?

Stock/availability requires shelf-specific evidence and usually region definitions, calibrated rules or a model trained for that task. The current generic COCO detector cannot reliably provide that evidence.

---

## Database & API Q&A

### 15. What are the main tables?

`users`, `analyses`, `detections`, and `shelf_regions` in the `retail_shelf_intelligence` schema.

### 16. How is ownership enforced?

The authenticated user ID is passed into repository queries. Reads and deletes require both the analysis ID and the authenticated user ID, rather than trusting an arbitrary client-supplied ID alone.

### 17. What happens if authentication is missing?

Protected analysis endpoints reject unauthenticated requests. The frontend also protects application routes and redirects unauthenticated users to login.

### 18. Why use multipart/form-data?

It is the standard HTTP representation for uploading binary files alongside form fields. It avoids encoding an image into JSON.

### 19. What does the API expose?

Health, create analysis, list analyses, get one analysis, and delete analysis endpoints under `/api`.

### 20. How does the frontend avoid exposing server secrets?

Only client-safe configuration such as the Supabase URL and publishable key is used in the frontend. Database credentials, JWT secrets and other server-only values remain in environment variables on the backend/deployment.

---

## Day 4 Feature Q&A

### 21. How does History search work?

The frontend filters the persisted analysis summaries by filename and can additionally filter by model. It then sorts the visible records by newest, oldest or detection count.

### 22. How does detail inspection work?

Each history row links to `/history?id=<analysis_id>`. The page requests the full analysis from the authenticated API and displays metadata plus each persisted detection's class, confidence and bounding-box coordinates.

### 23. How does CSV export work?

The browser builds a CSV from the currently visible history records or aggregated analytics, creates a temporary Blob URL, and starts a download. No server-side export endpoint is required for these views.

### 24. What happens when deleting a record?

The UI asks for confirmation first. If confirmed, it calls the authenticated delete endpoint, removes the deleted record from local state, and closes its detail view if that record was selected.

### 25. How is Analytics calculated?

Total analyses and total detections come from persisted analysis summaries. Class distribution is derived by loading persisted analysis details and aggregating their `class_counts`. The page then displays the top classes and their relative bar lengths.

### 26. Why is Analytics loading details separately?

The list endpoint provides summary information, while class-level distributions require the persisted `class_counts` from individual analysis records. The current implementation prioritizes correctness and uses the existing detail API.

---

## Security & Debugging Q&A

### 27. What upload security checks exist?

The application limits uploads to JPEG/PNG/WebP and 10 MB, checks filename extension and MIME/signature information, validates that OpenCV can decode the content, and uses an operating-system temporary file rather than trusting the client filename as a path.

### 28. What was an important integration issue?

The frontend initially experienced a browser `Failed to fetch` condition when communicating with the deployed backend. The integration was corrected by aligning the frontend API base configuration and production CORS origins. The backend was then reverified with authenticated requests and no recent runtime errors.

### 29. How would you debug a production 500?

First reproduce the failing request and identify its endpoint/status. Then inspect Vercel runtime logs, isolate whether the failure is authentication, input validation, model loading, database access or serialization, fix the smallest root cause, run CI, deploy, and re-test the same request.

### 30. How would you scale the analytics page?

The current frontend requests individual details for class aggregation. At larger scale I would move aggregation server-side, add pagination, index the relevant database fields, and expose an analytics endpoint that returns grouped counts in one request.

### 31. How would you improve the model?

Collect and label shelf-specific retail images, define SKU and shelf-region classes, split train/validation/test data carefully, fine-tune a detector, evaluate precision/recall and localization quality, then calibrate any inventory inference before exposing it in the UI.

### 32. How would you handle many concurrent uploads?

Move inference into an asynchronous job queue or worker system, persist job state, limit concurrency around CPU inference, and let the frontend poll or subscribe to job completion rather than holding a long synchronous request.

### 33. What would you monitor in production?

API latency, error rate, authentication failures, inference duration, model-load failures, database failures, upload rejection rates, analysis volume and resource usage.

### 34. What would you test beyond the current suite?

I would add API integration tests against a disposable database, frontend component tests, authenticated end-to-end browser tests, malformed image cases, oversized files, empty detection results, deletion authorization, and analytics correctness across multiple users.

---

## Deployment Q&A

### 35. How is deployment structured?

The repository remains one GitHub repository, while Vercel has separate frontend and backend projects. The frontend uses the production backend URL through `VITE_API_BASE_URL`.

### 36. What was actually verified?

GitHub Actions passed for the Day 4 commit. The latest frontend Vercel deployment reached `READY`, the production frontend returned HTTP 200, the backend health endpoint returned HTTP 200, and the production backend error/fatal log scan for the checked two-hour window was empty. The authenticated UI workflow was manually exercised.

---

## HR / Behavioral Questions

### Tell me about a challenge.

A key challenge was connecting a browser-authenticated React frontend to the deployed FastAPI service. I diagnosed the browser-level fetch failure rather than changing unrelated backend logic, aligned the API base/CORS configuration, redeployed, and then verified real authenticated requests and persistence.

### What did you learn?

I learned that computer-vision applications need evidence boundaries as much as model inference. A detector can produce accurate generic objects while still being unsuitable for a business claim such as out-of-stock status. I also learned the importance of tracing a request across frontend, authentication, API, model inference and database persistence.

### What would you improve?

The biggest improvement would be a shelf-specific model trained on labeled retail data. I would also move analytics aggregation server-side and add stronger automated end-to-end coverage.

### Why is this project resume-worthy?

It combines frontend engineering, REST APIs, authentication, database design, computer vision, model inference, security validation, CI and deployment in one working application. It also demonstrates the ability to state what a model can and cannot legitimately conclude.

---

## One-page rapid revision

**Project:** AI Retail Shelf Intelligence

**Frontend:** React + TypeScript + Vite + React Router

**Backend:** Python + FastAPI

**Vision:** OpenCV → YOLOX-Tiny → ONNX Runtime

**Database:** PostgreSQL / Supabase

**Auth:** Supabase Auth + bearer JWT

**Deployment:** Vercel

**CI:** GitHub Actions

**Input:** JPEG / PNG / WebP, max 10 MB

**Model input:** 416×416 letterbox

**Output:** boxes + COCO classes + confidence + counts + object coverage

**Tables:** users → analyses → detections / shelf_regions

**Day 4:** History search/filter/sort/detail/delete/CSV + Analytics/class distribution/CSV

**Evidence boundary:** no SKU, brand, inventory, availability, facing or out-of-stock claims

**Security:** upload validation + temporary files + JWT + user-scoped queries + no committed secrets

**Production:** frontend and backend deployed on Vercel; health/build/runtime checks verified

**Best architecture sentence:**

> React handles the user workflow, FastAPI orchestrates authenticated analysis, OpenCV prepares images, YOLOX-Tiny extracts generic visual detections, and PostgreSQL/Supabase persists evidence that the frontend turns into searchable history and analytics.
