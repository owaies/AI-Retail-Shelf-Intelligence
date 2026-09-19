# YOLOX-S Retail Fine-Tuning Runbook

This runbook covers the local training gate for the 62-class retail SKU detector. Training is intentionally local because the repository's free production services are not used for GPU training.

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

## What to record

Record the following from the run:

- epoch and training loss
- validation loss/metrics, if emitted by the trainer
- learning rate
- average step time
- peak allocated and reserved VRAM
- CUDA OOM or NaN/Inf events
- best checkpoint path
- exported model path, if ONNX export is enabled

## Data partition rules

- `train/` is used for optimization.
- `valid/` is used for validation and checkpoint selection.
- `test/` is held out until the model and training configuration are frozen.

Do not use test metrics to choose epochs, thresholds, augmentations, or checkpoints.

## After the short run

1. Confirm the checkpoint loads successfully.
2. Run a small inference sample against validation images.
3. Confirm predicted class IDs are in `0..61` and bounding boxes are finite and valid.
4. If the run is stable and learning, use measured throughput to choose a longer training duration.
5. Only after the training configuration is frozen, evaluate the held-out test split and report precision, recall, mAP@50, mAP@50:95, and per-class results.

## Artifact policy

Generated checkpoints and datasets stay outside Git. Keep them in the local `checkpoints/` and `benchmark/` paths covered by the repository ignore rules. Commit only source code, tests, configuration, and documentation needed to reproduce the workflow.

## Production boundary

The production Vercel application continues to use the lightweight runtime dependencies and ONNX Runtime inference path. Training-only PyTorch dependencies are kept separate in `backend/requirements-training.txt` so GPU training does not become a production deployment requirement.
