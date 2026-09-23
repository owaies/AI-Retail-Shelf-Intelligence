# Reproducible Retail Evaluation Protocol

This protocol defines the only supported path for reporting retail-SKU detector metrics in this repository.

## Dataset

Use the benchmark's `train/`, `valid/`, and `test/` partitions exactly as provided.

- Train: model optimization only.
- Valid: checkpoint/threshold selection only.
- Test: final held-out measurement only.

Do not copy test images into train/valid and do not tune the model after inspecting final test metrics.

## Vocabulary contract

The detector output vocabulary must equal the dataset vocabulary byte-for-byte in ordering and spelling.

The evaluator compares:

- number of classes;
- class names;
- class ordering.

A mismatch raises `VocabularyMismatchError`. There is no automatic COCO-to-SKU mapping.

## Model contract

Evaluation must use an explicit local `--model-path`.

This is deliberate:

- no hidden network dependency;
- no accidental model-version changes;
- no unexpected model download during a benchmark;
- the exact evaluated artifact can be recorded and archived outside Git.

For a retail detector, also provide `--model-vocab-yaml` describing that detector's output classes.

## Metrics

Class-aware evaluation reports:

- precision;
- recall;
- F1;
- mAP@50;
- mAP@50:95;
- TP, FP, FN;
- image, ground-truth, and prediction counts.

Class-agnostic evaluation is a localization diagnostic. It removes class equality from matching and therefore must never be described as SKU classification accuracy.

## Reproducibility record

Every final benchmark result should record:

1. model file and version;
2. model vocabulary;
3. dataset version and split;
4. confidence threshold;
5. IoU threshold;
6. evaluation mode;
7. metrics;
8. evaluation runtime;
9. software/runtime versions.

## Cost and artifact policy

The repository does not require downloading the benchmark dataset or model weights during ordinary CI.

Large datasets and model checkpoints remain outside Git. CI should execute unit/evaluation-contract tests and application smoke checks, not multi-hour GPU training or full retail benchmark inference.

The production application must not be changed merely to manufacture benchmark numbers. Retail-specific performance is only claimed after a genuine held-out evaluation.
