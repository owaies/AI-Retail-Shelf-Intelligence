# Production Change Boundary

Retail benchmark work must not be used to manufacture production accuracy claims.

The production application remains on its stable COCO baseline until a genuinely trained retail detector is available and evaluated on the untouched test split.

Evaluation-only changes may include:

- vocabulary validation;
- benchmark scripts;
- evaluation tests;
- reproducibility documentation;
- CI safety checks.

They must not silently:

- relabel COCO classes as retail SKUs;
- change production thresholds solely to improve an offline metric;
- bundle large model or dataset artifacts;
- claim SKU accuracy from class-agnostic localization;
- claim a deployment change that was not actually made.

This boundary keeps model-development evidence separate from production behavior.
