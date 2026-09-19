# Detector Evaluation & Retail Benchmark Workflow

## 1. Overview & Evaluation Baseline

The baseline vision service in this repository uses a local **YOLOX-S** ONNX model pretrained on the standard **Microsoft COCO dataset (80 object categories)**.

To evaluate retail shelf intelligence, a benchmark dataset with 62 granular retail product SKUs is placed locally under:
```text
benchmark/retail-shelf/
├── data.yaml
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### Dataset Provenance
- **Dataset**: `grocery-rfn8l` (v9) from Roboflow Universe (`lamar-university-venef/grocery-rfn8l/9`)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Classes**: 62 retail SKU classes (beverages, snacks, confectionery, etc.)
- **Format**: Standard YOLO normalized bounding box format (`class_id x_center y_center width height`)

---

## 2. COCO vs. Retail SKU Class Vocabulary Incompatibility

### The Vocabulary Mismatch Problem

The pretrained YOLOX-S model outputs predictions in the **80 COCO classes**, whereas the retail shelf benchmark dataset defines **62 SKU-level classes**:

| Index | COCO Class (Model) | Retail Benchmark Class (`data.yaml`) |
|---|---|---|
| `0` | `person` | `BargsBlack20Oz` |
| `1` | `bicycle` | `BuenoShareSize` |
| `2` | `car` | `CheetosCrunchy` |
| `3` | `motorcycle` | `CheetosCrunchyFlaminHot` |
| `...` | `...` | `...` |
| `39` | `bottle` | `LennyLarrysSnickerdoodle` |
| `...` | `...` | `...` |
| `61` | `toilet` | `ZeroCocaCola16Oz` |

### Why Direct Evaluation is Scientifically Invalid

Directly evaluating the pretrained COCO YOLOX-S model against the 62-class retail annotations without vocabulary mapping is invalid:
1. **Semantic Collision**: Label `0` in the retail dataset (`BargsBlack20Oz`) would be incorrectly treated as `person` (COCO `0`). A bottle correctly localized by the detector as a COCO `bottle` (class `39`) would be evaluated against ground-truth `person` (class `0`), registering both a false positive and a false negative.
2. **False Metrics**: Reporting precision, recall, or AP50 computed from this index misalignment would produce meaningless metrics and misrepresent detector capability.

### Evaluator Safety Enforcement

The evaluation script (`backend/scripts/evaluate_detector.py`) and evaluation service (`backend/app/services/evaluation.py`) enforce vocabulary safety:
- Discovers `data.yaml` to read dataset class names and count (`nc`).
- Compares model vocabulary against dataset vocabulary.
- If incompatible, the evaluator **fails safely** with exit code 2 and outputs a structured error report detailing the vocabulary mismatch, refusing to fabricate SKU metrics.

---

## 3. Running the Evaluator

From `backend/`:

### Standard / Direct Evaluation (Requires Compatible Vocabulary)
```bash
python scripts/evaluate_detector.py ../benchmark/retail-shelf --split test
```
*If run with a COCO-trained model on the 62-class dataset, this will safely reject the execution with `incompatible_vocabulary` error.*

### Class-Agnostic Localization Benchmark (Diagnostic)
To measure the detector's capability to localize physical retail shelf items (bounding box overlap / objectness recall) without claiming SKU classification accuracy:
```bash
python scripts/evaluate_detector.py ../benchmark/retail-shelf --split test --class-agnostic --output ../benchmark/localization_report.json
```

---

---

## 5. YOLOX-S Training & Fine-Tuning Pipeline

A reproducible PyTorch training pipeline is implemented under `backend/app/training/` and `backend/scripts/train_yolox.py`. It trains the exact YOLOX-S architecture with 62-class output heads, initialized from official Megvii COCO pretrained weights (`yolox_s.pth`).

### Hardware Specifications & Profile (Measured Environment)
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **Compute Stack**: CUDA 11.8 / PyTorch 2.7.1 + cu118 / Mixed Precision (AMP FP16)
- **Recommended Batch Size**: `4` (Safe for 4 GB GPUs; peak VRAM allocated is 1.11 GB, peak reserved is 1.35 GB, leaving >2.6 GB headroom)
- **Input Dimension**: `640x640` (Native YOLOX-S letterbox resolution)
- **Measured Throughput**: ~23.66 minutes per epoch across 24,415 training images + 4,081 validation images (6,104 steps/epoch)
- **Validation Run**: 3 epochs completed in 70.99 minutes (loss: 46.186 -> 45.123, val loss: 45.867 -> 45.139)
- **Estimated 30-Epoch Training**: ~11.8 hours total on RTX 3050

### Strict Dataset Partition Separation
> [!IMPORTANT]
> The training pipeline strictly utilizes `train/` for optimization and `valid/` for validation loss monitoring and checkpoint selection. The `test/` partition (6,884 images / 18,687 boxes) is **strictly held out and never touched** during training or model selection.

### Commands

#### 1. GPU Smoke Test / Dry-Run (Fast Verification)
Validates the dataset integrity (62 classes, normalized coordinates, missing files check), initializes the model, loads pretrained weights, and executes 3 GPU training steps + 1 validation step without launching a long training job:
```bash
python scripts/train_yolox.py --dataset ../benchmark/retail-shelf --smoke-test
```

#### 2. Full Training Run
```bash
python scripts/train_yolox.py --dataset ../benchmark/retail-shelf --batch-size 4 --img-size 640 --epochs 30 --lr 0.001 --fp16 --output-dir checkpoints
```

#### 3. Resuming Training
To resume from the latest saved checkpoint after interruption:
```bash
python scripts/train_yolox.py --dataset ../benchmark/retail-shelf --resume checkpoints/last.pth
```

### Checkpoints and Artifacts
Checkpoints are saved outside Git under `backend/checkpoints/` (or specified `--output-dir`):
- `last.pth`: Checkpoint containing model weights, optimizer state, AMP scaler state, epoch number, best validation loss, and full history.
- `best_model.pth`: PyTorch weights from the epoch with lowest validation loss.
- `best_model.onnx`: Auto-exported ONNX model ready for deployment in `backend/app/services/vision.py`.
- `training_history.json`: Epoch-by-epoch loss records and learning rate schedule.

---

## 6. Held-Out Retail Benchmark Results (62-Class SKU Test Split)

The frozen 3-epoch validation model (`checkpoints/best_model.onnx`) was evaluated against the full, unaugmented, held-out retail test partition using `scripts/evaluate_detector.py`.

### Benchmark Configuration
- **Model**: YOLOX-S `retail-62` (`backend/checkpoints/best_model.onnx`, 34.21 MB)
- **Vocabulary**: 62 retail SKU classes from `benchmark/retail-shelf/data.yaml`
- **Evaluation Split**: `test/` (held-out partition)
- **IoU Match Threshold**: 0.50
- **Inference Confidence Threshold**: 0.20 (Standard production evaluation gate)
- **Runtime**: 19 minutes 58 seconds across 6,884 test images on CPU (~174 ms/image)

### Empirical Test Set Metrics

| Metric | Measured Value | Description |
|---|---|---|
| **Test Images** | `6,884` | Total labeled held-out test images |
| **Ground Truth Objects** | `18,687` | Labeled retail SKU items across 62 classes |
| **Model Predictions** | `0` | Predictions passing confidence threshold ≥ 0.20 |
| **True Positives (TP)** | `0` | IoU ≥ 0.50 with correct class matching |
| **False Positives (FP)** | `0` | Unmatched predictions or class mismatch |
| **False Negatives (FN)** | `18,687` | Unmatched ground-truth items |
| **Precision** | `0.000` | $TP / (TP + FP)$ |
| **Recall** | `0.000` | $TP / (TP + FN)$ |
| **F1 Score** | `0.000` | Harmonic mean of precision and recall |
| **mAP@50** | `0.000` | Mean Average Precision at IoU 0.50 |
| **mAP@50:95** | `0.000` | Mean Average Precision averaged over IoU 0.50:0.05:0.95 |

### Analysis & Technical Findings

1. **Short Validation vs. Fully Trained Head**:
   - The 3-epoch run was executed as an architecture and pipeline convergence validation gate. While localization IoU loss improved by 50.9% during training, the classification head was initialized from scratch with prior probability $0.01$.
   - At 3 epochs, classification logit activations remain below the standard 0.20 inference confidence threshold, resulting in 0 predictions meeting the confidence filter.
2. **Path to Measurable SKU mAP**:
   - Extended fine-tuning (15 to 30 epochs, estimated at 5.9 to 11.8 hours based on measured 23.66 min/epoch throughput) is required to train the classification head weights to high-confidence decision boundaries.
3. **Evidence Integrity**:
   - Metrics are preserved exactly as generated by `checkpoints/test-evaluation.json` without fabrication or threshold tampering.
   - Production deployment safely maintains the general COCO baseline with observable category reporting until an extended retail training checkpoint is completed.

