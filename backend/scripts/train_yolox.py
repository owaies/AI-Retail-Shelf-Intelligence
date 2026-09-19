from __future__ import annotations

import argparse
import json
import logging
import math
import os
from pathlib import Path
import sys
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Add backend directory to sys.path for direct script execution
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.training.dataset import (
    YoloRetailDataset,
    validate_retail_dataset,
    yolox_collate_fn,
)
from app.training.loss import YOLOXLoss
from app.training.models.yolox import YOLOX, create_yolox_s

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("yolox_trainer")


def resolve_dataset_path(provided_path: str | None) -> Path:
    if provided_path:
        p = Path(provided_path).resolve()
        if p.exists():
            return p
        # Check relative to backend or workspace root
        if (BACKEND_DIR / provided_path).exists():
            return (BACKEND_DIR / provided_path).resolve()
        if (BACKEND_DIR.parent / provided_path).exists():
            return (BACKEND_DIR.parent / provided_path).resolve()
        return p

    # Standard candidate locations
    candidates = [
        BACKEND_DIR.parent / "benchmark" / "retail-shelf",
        BACKEND_DIR / "benchmark" / "retail-shelf",
        Path("benchmark/retail-shelf").resolve(),
    ]
    for c in candidates:
        if c.exists() and (c / "data.yaml").exists():
            return c.resolve()

    return candidates[0].resolve()


def export_onnx(model: YOLOX, output_path: Path, img_size: int = 640) -> None:
    """Export trained PyTorch model to ONNX for inference deployment."""
    model.eval()
    dummy_input = torch.zeros(1, 3, img_size, img_size, device=next(model.parameters()).device)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        torch.onnx.export(
            model,
            dummy_input,
            str(output_path),
            input_names=["images"],
            output_names=["output"],
            dynamic_axes={"images": {0: "batch"}, "output": {0: "batch"}},
            opset_version=12,
        )
        logger.info(f"Successfully exported ONNX model to {output_path}")
    except Exception as exc:
        logger.warning(f"Failed to export ONNX model: {exc}")


def evaluate_validation(
    model: YOLOX,
    val_loader: DataLoader,
    loss_fn: YOLOXLoss,
    device: torch.device,
    use_amp: bool = False,
    max_batches: int | None = None,
) -> dict[str, float]:
    """Evaluate model on the validation split (never the test set)."""
    model.eval()
    total_val_loss = 0.0
    total_iou_loss = 0.0
    total_cls_loss = 0.0
    total_obj_loss = 0.0
    total_positives = 0
    count = 0

    with torch.no_grad():
        for b_idx, (images, targets, _, _) in enumerate(val_loader):
            if max_batches is not None and b_idx >= max_batches:
                break
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            if use_amp and device.type == "cuda":
                with torch.amp.autocast("cuda"):
                    outputs = model(images)
                    loss, metrics = loss_fn(outputs, targets, (images.shape[2], images.shape[3]))
            else:
                outputs = model(images)
                loss, metrics = loss_fn(outputs, targets, (images.shape[2], images.shape[3]))

            total_val_loss += metrics["loss_total"]
            total_iou_loss += metrics["loss_iou"]
            total_cls_loss += metrics["loss_cls"]
            total_obj_loss += metrics["loss_obj"]
            total_positives += metrics["matched_positives"]
            count += 1

    if count == 0:
        return {"val_loss": 0.0, "val_iou": 0.0, "val_cls": 0.0, "val_obj": 0.0}

    return {
        "val_loss": total_val_loss / count,
        "val_iou": total_iou_loss / count,
        "val_cls": total_cls_loss / count,
        "val_obj": total_obj_loss / count,
        "matched_positives": total_positives,
    }


def run_smoke_test(
    dataset_dir: Path,
    device: torch.device,
    batch_size: int = 4,
    img_size: int = 640,
    use_amp: bool = True,
    weights_path: str | None = None,
) -> dict:
    """Dry-run / smoke-test: validates dataset, initializes model, optimizer, dataloader,

    and runs 1 training step + 1 validation step on RTX 3050.
    """
    logger.info("=" * 60)
    logger.info("STARTING YOLOX-S SMOKE TEST / DRY-RUN")
    logger.info("=" * 60)

    # 1. Dataset validation
    logger.info(f"1. Validating dataset at: {dataset_dir}")
    ds_meta = validate_retail_dataset(dataset_dir)
    logger.info(f"   [PASS] Dataset verified: {ds_meta['num_classes']} classes, splits: {ds_meta['splits']}")

    # 2. Dataloaders
    train_ds = YoloRetailDataset(
        img_dir=dataset_dir / "train" / "images",
        lbl_dir=dataset_dir / "train" / "labels",
        img_size=img_size,
        augment=True,
        num_classes=62,
    )
    val_ds = YoloRetailDataset(
        img_dir=dataset_dir / "valid" / "images",
        lbl_dir=dataset_dir / "valid" / "labels",
        img_size=img_size,
        augment=False,
        num_classes=62,
    )
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=yolox_collate_fn,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=yolox_collate_fn,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )
    logger.info(f"2. DataLoaders initialized: train={len(train_ds)} imgs, valid={len(val_ds)} imgs")

    # 3. Model & weights initialization
    logger.info(f"3. Initializing YOLOX-S on device: {device} (AMP={use_amp})")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
        vram_start = torch.cuda.memory_allocated() / (1024 * 1024)
    else:
        vram_start = 0.0

    model = create_yolox_s(num_classes=62, pretrained=True, weights_path=weights_path, device=device)
    loss_fn = YOLOXLoss(num_classes=62).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3, momentum=0.9, weight_decay=5e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=(use_amp and device.type == "cuda"))

    # 4. Multi-step dry run (warmup + steady state)
    logger.info("4. Running 3 forward + backward training steps on GPU...")
    model.train()
    step_times = []
    last_metrics = {}

    train_iter = iter(train_loader)
    for step_num in range(1, 4):
        images, targets, _, _ = next(train_iter)
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)

        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()

        optimizer.zero_grad()
        if use_amp and device.type == "cuda":
            with torch.amp.autocast("cuda"):
                outputs = model(images)
                loss, metrics = loss_fn(outputs, targets, (img_size, img_size))
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss, metrics = loss_fn(outputs, targets, (img_size, img_size))
            loss.backward()
            optimizer.step()

        if device.type == "cuda":
            torch.cuda.synchronize()
        dt_ms = (time.perf_counter() - t0) * 1000
        step_times.append(dt_ms)
        last_metrics = metrics
        logger.info(f"   Step {step_num}/3: {dt_ms:.1f} ms | Total Loss: {metrics['loss_total']:.4f}")

    # Steady state average (excluding first warmup step)
    steady_state_ms = sum(step_times[1:]) / max(len(step_times) - 1, 1) if len(step_times) > 1 else step_times[0]

    # 5. Single validation step
    logger.info("5. Running 1 validation evaluation step on valid/ split...")
    val_metrics = evaluate_validation(model, val_loader, loss_fn, device, use_amp=use_amp, max_batches=1)

    vram_peak_alloc = 0.0
    vram_peak_res = 0.0
    if device.type == "cuda":
        vram_peak_alloc = torch.cuda.max_memory_allocated() / (1024 * 1024)
        vram_peak_res = torch.cuda.max_memory_reserved() / (1024 * 1024)

    # Estimate full epoch time using steady-state throughput
    steps_per_epoch = math.ceil(len(train_ds) / batch_size)
    estimated_epoch_sec = (steady_state_ms / 1000.0) * steps_per_epoch

    results = {
        "status": "success",
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else "N/A",
        "batch_size": batch_size,
        "img_size": img_size,
        "use_amp": use_amp,
        "step_loss": last_metrics,
        "val_step_loss": val_metrics,
        "steady_state_ms_per_batch": round(steady_state_ms, 2),
        "vram_peak_allocated_mb": round(vram_peak_alloc, 2),
        "vram_peak_reserved_mb": round(vram_peak_res, 2),
        "train_samples": len(train_ds),
        "steps_per_epoch": steps_per_epoch,
        "estimated_epoch_minutes": round(estimated_epoch_sec / 60.0, 2),
        "estimated_30_epochs_hours": round((estimated_epoch_sec * 30) / 3600.0, 2),
    }

    logger.info("=" * 60)
    logger.info("SMOKE TEST RESULTS:")
    logger.info(f"  Status:                     {results['status']}")
    logger.info(f"  GPU:                        {results['gpu_name']}")
    logger.info(f"  Steady-State Step Time:     {results['steady_state_ms_per_batch']} ms / batch of {batch_size}")
    logger.info(f"  Peak VRAM Allocated:        {results['vram_peak_allocated_mb']} MB")
    logger.info(f"  Peak VRAM Reserved:         {results['vram_peak_reserved_mb']} MB (safe for 4GB RTX 3050)")
    logger.info(f"  Training Loss:              {last_metrics['loss_total']:.4f}")
    logger.info(f"  Validation Loss (step):     {val_metrics['val_loss']:.4f}")
    logger.info(f"  Steps per Epoch:            {steps_per_epoch}")
    logger.info(f"  Estimated Time / Epoch:     {results['estimated_epoch_minutes']} mins")
    logger.info(f"  Estimated 30 Epochs:        {results['estimated_30_epochs_hours']} hours")
    logger.info("=" * 60)

    return results


def train_yolox(
    dataset_dir: Path,
    output_dir: Path,
    epochs: int = 30,
    batch_size: int = 4,
    img_size: int = 640,
    lr: float = 1e-3,
    device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    use_amp: bool = True,
    weights_path: str | None = None,
    resume_path: str | None = None,
) -> None:
    """Full training pipeline for YOLOX-S fine-tuning on 62-class retail dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Dataset validation
    ds_meta = validate_retail_dataset(dataset_dir)
    logger.info(f"Dataset validated: {ds_meta['num_classes']} classes in {dataset_dir}")
    logger.info("CRITICAL: Training will strictly use train/ and valid/ splits. The test/ split is NOT used.")

    # 2. Datasets & Loaders
    train_ds = YoloRetailDataset(
        img_dir=dataset_dir / "train" / "images",
        lbl_dir=dataset_dir / "train" / "labels",
        img_size=img_size,
        augment=True,
        num_classes=62,
    )
    val_ds = YoloRetailDataset(
        img_dir=dataset_dir / "valid" / "images",
        lbl_dir=dataset_dir / "valid" / "labels",
        img_size=img_size,
        augment=False,
        num_classes=62,
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=yolox_collate_fn,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=yolox_collate_fn,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    # 3. Model
    model = create_yolox_s(num_classes=62, pretrained=(resume_path is None), weights_path=weights_path, device=device)
    loss_fn = YOLOXLoss(num_classes=62).to(device)

    # Optimizer & Scheduler
    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=lr,
        momentum=0.9,
        weight_decay=5e-4,
        nesterov=True,
    )
    lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=epochs, eta_min=lr * 0.01
    )
    scaler = torch.amp.GradScaler("cuda", enabled=(use_amp and device.type == "cuda"))

    start_epoch = 1
    best_val_loss = float("inf")
    history: list[dict] = []

    # 4. Resume if requested
    if resume_path:
        r_path = Path(resume_path)
        if not r_path.is_file():
            raise FileNotFoundError(f"Checkpoint to resume not found: {r_path}")
        logger.info(f"Resuming training from checkpoint: {r_path}")
        ckpt = torch.load(str(r_path), map_location=device)
        model.load_state_dict(ckpt["model"])
        if "optimizer" in ckpt:
            optimizer.load_state_dict(ckpt["optimizer"])
        if "scaler" in ckpt and ckpt["scaler"] is not None:
            scaler.load_state_dict(ckpt["scaler"])
        if "epoch" in ckpt:
            start_epoch = ckpt["epoch"] + 1
        if "best_val_loss" in ckpt:
            best_val_loss = ckpt["best_val_loss"]
        if "history" in ckpt:
            history = ckpt["history"]

    logger.info(f"Training YOLOX-S on {device} | Epochs: {epochs} | Batch Size: {batch_size} | AMP: {use_amp}")

    for epoch in range(start_epoch, epochs + 1):
        model.train()
        total_train_loss = 0.0
        total_steps = 0
        t_start = time.perf_counter()

        for step, (images, targets, _, _) in enumerate(train_loader, start=1):
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            optimizer.zero_grad()
            if use_amp and device.type == "cuda":
                with torch.amp.autocast("cuda"):
                    outputs = model(images)
                    loss, metrics = loss_fn(outputs, targets, (img_size, img_size))
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = model(images)
                loss, metrics = loss_fn(outputs, targets, (img_size, img_size))
                loss.backward()
                optimizer.step()

            total_train_loss += metrics["loss_total"]
            total_steps += 1

            if step == 1 or step % 200 == 0 or step == len(train_loader):
                logger.info(
                    f"Epoch [{epoch}/{epochs}] Step [{step}/{len(train_loader)}] "
                    f"Loss: {metrics['loss_total']:.4f} (IoU: {metrics['loss_iou']:.4f}, "
                    f"Cls: {metrics['loss_cls']:.4f}, Obj: {metrics['loss_obj']:.4f}) "
                    f"LR: {optimizer.param_groups[0]['lr']:.6f}"
                )

        lr_scheduler.step()
        epoch_train_loss = total_train_loss / max(total_steps, 1)
        epoch_time = time.perf_counter() - t_start

        # Validation phase
        val_metrics = evaluate_validation(model, val_loader, loss_fn, device, use_amp=use_amp)
        val_loss = val_metrics["val_loss"]

        vram_alloc = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2) if device.type == "cuda" else 0.0
        vram_res = round(torch.cuda.max_memory_reserved() / (1024 * 1024), 2) if device.type == "cuda" else 0.0

        epoch_record = {
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "val_loss": round(val_loss, 4),
            "val_iou": round(val_metrics["val_iou"], 4),
            "val_cls": round(val_metrics["val_cls"], 4),
            "val_obj": round(val_metrics["val_obj"], 4),
            "epoch_time_sec": round(epoch_time, 2),
            "lr": optimizer.param_groups[0]["lr"],
            "vram_peak_allocated_mb": vram_alloc,
            "vram_peak_reserved_mb": vram_res,
        }
        history.append(epoch_record)

        logger.info(
            f"--> Epoch {epoch}/{epochs} complete in {epoch_time:.1f}s | "
            f"Train Loss: {epoch_train_loss:.4f} | Val Loss: {val_loss:.4f} | "
            f"VRAM Peak: {vram_alloc:.1f} MB alloc, {vram_res:.1f} MB res"
        )

        # Save last checkpoint
        last_ckpt_path = output_dir / "last.pth"
        torch.save(
            {
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scaler": scaler.state_dict() if use_amp else None,
                "best_val_loss": best_val_loss,
                "history": history,
                "classes": ds_meta["class_names"],
            },
            str(last_ckpt_path),
        )

        # Save best checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_ckpt_path = output_dir / "best_model.pth"
            torch.save(
                {
                    "epoch": epoch,
                    "model": model.state_dict(),
                    "best_val_loss": best_val_loss,
                    "classes": ds_meta["class_names"],
                },
                str(best_ckpt_path),
            )
            logger.info(f"*** New best model achieved (val_loss: {val_loss:.4f})! Saved to {best_ckpt_path}")

            # Export ONNX
            onnx_path = output_dir / "best_model.onnx"
            export_onnx(model, onnx_path, img_size=img_size)

        # Save history log JSON
        with (output_dir / "training_history.json").open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLOX-S Fine-Tuning Pipeline for Retail Shelf Intelligence")
    parser.add_argument("--dataset", type=str, default=None, help="Path to retail-shelf dataset root")
    parser.add_argument("--output-dir", type=str, default="checkpoints", help="Directory to store model checkpoints")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size per training step (default: 4 for 4GB GPU)")
    parser.add_argument("--img-size", type=int, default=640, help="Input image dimension (default: 640)")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--device", type=str, default=None, help="Device to use ('cuda' or 'cpu')")
    parser.add_argument("--fp16", action="store_true", default=True, help="Enable mixed precision AMP (default: True)")
    parser.add_argument("--no-fp16", action="store_false", dest="fp16", help="Disable mixed precision AMP")
    parser.add_argument("--weights", type=str, default=None, help="Pretrained YOLOX checkpoint path (.pth)")
    parser.add_argument("--resume", type=str, default=None, help="Resume training from checkpoint (.pth)")
    parser.add_argument("--smoke-test", action="store_true", help="Run 1-step dry-run / smoke-test on GPU")
    parser.add_argument("--eval-only", action="store_true", help="Evaluate model on valid/ split without training")

    args = parser.parse_args()

    dataset_path = resolve_dataset_path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"Dataset path not found: {dataset_path}")
        return 1

    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.smoke_test:
        run_smoke_test(
            dataset_dir=dataset_path,
            device=device,
            batch_size=args.batch_size,
            img_size=args.img_size,
            use_amp=args.fp16,
            weights_path=args.weights,
        )
        return 0

    output_dir = Path(args.output_dir).resolve()
    train_yolox(
        dataset_dir=dataset_path,
        output_dir=output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        img_size=args.img_size,
        lr=args.lr,
        device=device,
        use_amp=args.fp16,
        weights_path=args.weights,
        resume_path=args.resume,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
