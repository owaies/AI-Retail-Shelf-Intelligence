# CI Evaluation Scope

GitHub Actions verifies the evaluation implementation without running the full retail benchmark.

CI covers:

- Python compilation;
- the complete pytest suite;
- the evaluation-contract tests;
- FastAPI health startup;
- frontend production build.

CI intentionally does not:

- download the retail dataset;
- download detector weights;
- run multi-hour GPU fine-tuning;
- run the 6,884-image held-out benchmark.

This keeps CI deterministic, reasonably fast, and free of unnecessary large downloads while still testing the safety boundary that protects benchmark validity.
