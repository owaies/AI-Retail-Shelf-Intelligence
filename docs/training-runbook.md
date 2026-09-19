# YOLOX-S Retail Fine-Tuning Runbook

This runbook covers the local training and held-out evaluation gates for the 62-class retail SKU detector. Training and benchmarking are intentionally local because the repository's free production services are not used for GPU training.

## Preconditions

- Repository: `owaies/AI-Retail-Shelf-Intelligence`
- Dataset: `benchmark/retail-shelf`
- Dataset vocabulary: 62 retail SKU classes from `data.yaml`
- GPU target: NVIDIA RTX 3050 Laptop GPU, 4 GB VRAM
- Recommended starting configuration: YOLOX-S, `640x640`, batch size `4`, AMP/FP16
- Do not place dataset images, labels, checkpoints, `.pth`, or generated `.onnx` artifacts in Git.

## Short validation run

From `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\train_yolox.py `
  --dataset ../benchmark/retail-shelf `
  --epochs 3 `
  --batch-size 4 `
  --img-size 640 `
  --lr 0.001 `
  --fp16 `
  --output-dir checkpoints
```

The purpose of this run is to verify that real retail fine-tuning is stable and that validation loss/checkpoint behavior is sensible before committing to a long run. It is not a final accuracy benchmark.

## Measured 3-Epoch Validation Results

The 3-epoch fine-tuning run was executed on the local NVIDIA RTX 3050 Laptop GPU (4 GB VRAM) using mixed precision (AMP FP16), batch size 4, and native 640×640 image size.

### Hardware & Environment
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4.00 GB VRAM)
- **Framework**: PyTorch 2.7.1 + CUDA 11.8
- **Dataset**: `benchmark/retail-shelf` (24,415 train images, 4,081 valid images, 62 SKU classes)
- **Batch Size**: 4 (6,104 optimization steps per epoch)
- **Mixed Precision**: Enabled (PyTorch `torch.amp.autocast`)

### Epoch Progression

| Epoch | Train Loss | Val Loss | Val IoU Loss | Val Cls Loss | Val Obj Loss | Epoch Time | Learning Rate | Peak VRAM Alloc | Peak VRAM Res |
|---|---|---|---|---|---|---|---|---|---|
| **1** | 46.1860 | 45.8669 | 1.3977 | 42.9818 | 1.4874 | 1,516.2 s (25.3 min) | 0.000752 | 1,106.1 MB | 1,266.0 MB |
| **2** | 45.4558 | 45.4268 | 0.9658 | 42.9804 | 1.4806 | 1,330.6 s (22.2 min) | 0.000258 | 1,106.1 MB | 1,348.0 MB |
| **3** | 45.1229 | 45.1390 | 0.6863 | 42.9792 | 1.4734 | 1,412.5 s (23.5 min) | 0.000010 | 1,106.1 MB | 1,350.0 MB |

- **Total Training Time**: 4,259.3 seconds (~70.99 minutes / 1.18 hours)
- **Average Epoch Duration**: ~23.66 minutes (including full 4,081-image validation pass)
- **Stability**: Zero NaN/Inf occurrences; zero CUDA OOM errors; stable VRAM footprint (<1.35 GB reserved vs 4 GB limit).
- **Bounding Box Convergence**: Validation IoU loss improved over the three-epoch run (1.3977 down to 0.6863).

### Checkpoint & Model Verification
- **Artifacts Saved**:
  - `backend/checkpoints/best_model.pth` (36.1 MB, lowest val loss: `45.1390`)
  - `backend/checkpoints/best_model.onnx` (35.9 MB, 62-class output shape `[1, 8400, 67]`)
  - `backend/checkpoints/last.pth` (72.0 MB, full model, optimizer, scaler, and history)
  - `backend/checkpoints/training_history.json`
- **Validation Sample Inference**:
  - Successfully loaded `best_model.pth` using `create_yolox_s(num_classes=62)`.
  - Executed inference on 5 validation samples.
  - Verified: all coordinates finite, confidences in `[0, 1]`, and predicted class IDs strictly in `[0, 61]`.

## Held-Out Test Benchmark

Run this only after the training configuration and checkpoint are frozen. The benchmark supports the local trained 62-class ONNX model and the matching retail vocabulary.

From `backend/`:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_detector.py `
  ../benchmark/retail-shelf `
  --split test `
  --model-path checkpoints/best_model.onnx `
  --model-vocab-yaml ../benchmark/retail-shelf/data.yaml `
  --output checkpoints/test-evaluation.json
```

The evaluator verifies the model vocabulary against the dataset vocabulary before class-aware SKU evaluation. It reports:

- Precision
- Recall
- F1
- mAP@50
- mAP@50:95
- TP / FP / FN
- image, ground-truth, and prediction counts

The test split must not be used to choose epochs, confidence thresholds, augmentation, or checkpoints.

For the legacy COCO production detector, `--class-agnostic` is available only as a localization diagnostic. Its result must not be presented as SKU recognition accuracy.

## Data partition rules

- `train/` is used for optimization.
- `valid/` is used for validation and checkpoint selection.
- `test/` is held out until the model and training configuration are frozen.

## Long Run Recommendation

Based on the measured throughput of **23.66 minutes per epoch**:
- A **15-epoch** fine-tuning run is estimated at **~5.9 hours**.
- A **30-epoch** fine-tuning run is estimated at **~11.8 hours**.

The 3-epoch validation confirms the pipeline, loss calculation, memory safety, checkpoint preservation, and inference output shape. It does not establish final SKU accuracy.

## Artifact policy

Generated checkpoints and datasets stay outside Git. Keep them in the local `checkpoints/` and `benchmark/` paths covered by the repository ignore rules. Commit only source code, tests, configuration, and documentation needed to reproduce the workflow.

## Production boundary

The production Vercel application continues to use the lightweight runtime dependencies and ONNX Runtime inference path. Training-only PyTorch dependencies are kept separate in `backend/requirements-training.txt` so GPU training does not become a production deployment requirement.
