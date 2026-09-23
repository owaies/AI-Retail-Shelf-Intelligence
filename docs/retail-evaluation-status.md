# Retail Detector Evaluation Status

## Current production baseline

The deployed detector is the official YOLOX-S COCO checkpoint. Its 80-class vocabulary is not the same as the 62-class retail SKU benchmark vocabulary.

Therefore the production baseline is **not a SKU classifier**. It reports observable COCO categories only.

## Retail evaluation requirement

A valid SKU evaluation requires all of the following:

1. A detector trained for the 62 retail classes.
2. A model vocabulary file whose class ordering exactly matches the benchmark `data.yaml`.
3. Evaluation on the untouched `test/` split.
4. A fixed confidence and IoU configuration recorded with the result.
5. No class-index reinterpretation between COCO and retail labels.

The evaluator now rejects incompatible vocabularies before inference and requires an explicit local model path. Benchmark execution never downloads model weights implicitly.

## Why the limitation matters

Mapping COCO class IDs directly onto retail SKU IDs would turn unrelated labels into apparently valid predictions. The resulting precision, recall, F1, and AP values would not measure the claimed task.

The safe alternatives are:

- **Retail SKU evaluation:** use the fine-tuned retail detector and its matching vocabulary.
- **Localization diagnostic:** use a locally available detector with `--class-agnostic`; this measures box overlap/object localization only and must not be presented as SKU accuracy.

## Current benchmark interpretation

The repository contains a documented 3-epoch retail fine-tuning/evaluation result. That run produced zero predictions at the production confidence threshold and is therefore not evidence of useful SKU classification accuracy.

An extended fine-tuning run is required before claiming retail classification performance. The held-out test split must remain untouched until the final model and threshold are fixed.

## Reproducibility

Run from `backend/` with an explicit local detector:

```bash
python scripts/evaluate_detector.py ../benchmark/retail-shelf \
  --split test \
  --model-path ../checkpoints/best_model.onnx \
  --model-vocab-yaml ../benchmark/retail-shelf/data.yaml \
  --output ../benchmark/test-evaluation.json
```

For a class-agnostic localization diagnostic, use the same explicit model path with `--class-agnostic`. The report will identify the mode so localization results cannot be mistaken for SKU metrics.
