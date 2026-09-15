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

### Hardware Specifications & Profile (Tested Environment)
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **Compute Stack**: CUDA 13.0 Driver / PyTorch 2.7.1 + cu118 / Mixed Precision (AMP FP16)
- **Recommended Batch Size**: `4` (Safe for 4 GB GPUs; peak VRAM reserved is ~1.27 GB, leaving >2.7 GB headroom)
- **Input Dimension**: `640x640` (Native YOLOX-S letterbox resolution)
- **Steady-State Throughput**: ~225 ms per batch of 4 on RTX 3050
- **Epoch Duration**: ~22.8 minutes per epoch across 24,415 training images (6,104 steps/epoch)
- **Estimated 30-Epoch Training**: ~11.4 hours total on RTX 3050

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

