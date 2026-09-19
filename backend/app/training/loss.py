from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class IOUloss(nn.Module):
    def __init__(self, reduction: str = "none", loss_type: str = "iou") -> None:
        super().__init__()
        self.reduction = reduction
        self.loss_type = loss_type

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # pred, target: [N, 4] in (x1, y1, x2, y2)
        assert pred.shape[0] == target.shape[0]

        tl = torch.max(pred[:, :2], target[:, :2])
        br = torch.min(pred[:, 2:], target[:, 2:])
        area_p = torch.prod(pred[:, 2:] - pred[:, :2], 1)
        area_g = torch.prod(target[:, 2:] - target[:, :2], 1)

        en = (tl < br).type(tl.type()).prod(dim=1)
        area_i = torch.prod(br - tl, 1) * en
        area_u = area_p + area_g - area_i
        iou = (area_i) / (area_u + 1e-16)

        if self.loss_type == "iou":
            loss = 1.0 - iou ** 2
        elif self.loss_type == "giou":
            c_tl = torch.min(pred[:, :2], target[:, :2])
            c_br = torch.max(pred[:, 2:], target[:, 2:])
            area_c = torch.prod(c_br - c_tl, 1)
            giou = iou - (area_c - area_u) / (area_c + 1e-16)
            loss = 1.0 - giou.clamp(min=-1.0, max=1.0)
        else:
            loss = 1.0 - iou

        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


class YOLOXLoss(nn.Module):
    """Anchor-free loss module for YOLOX training with IoU, Objectness and Classification losses."""

    def __init__(
        self,
        num_classes: int = 62,
        strides: tuple[int, ...] = (8, 16, 32),
        reg_weight: float = 5.0,
        obj_weight: float = 1.0,
        cls_weight: float = 1.0,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.strides = strides
        self.reg_weight = reg_weight
        self.obj_weight = obj_weight
        self.cls_weight = cls_weight
        self.iou_loss = IOUloss(reduction="none", loss_type="iou")
        self.bce_loss = nn.BCEWithLogitsLoss(reduction="none")

    def _generate_grids_and_strides(
        self, input_h: int, input_w: int, device: torch.device
    ) -> tuple[torch.Tensor, torch.Tensor]:
        grids = []
        strides = []
        for stride in self.strides:
            hs, ws = input_h // stride, input_w // stride
            yv, xv = torch.meshgrid(
                torch.arange(hs, device=device),
                torch.arange(ws, device=device),
                indexing="ij",
            )
            grid = torch.stack((xv, yv), dim=2).view(1, -1, 2)
            grids.append(grid)
            strides.append(torch.full((1, hs * ws, 1), stride, device=device, dtype=torch.float32))

        return torch.cat(grids, dim=1), torch.cat(strides, dim=1)

    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        img_size: tuple[int, int] = (640, 640),
    ) -> tuple[torch.Tensor, dict[str, float]]:
        """
        predictions: [B, num_anchors, 4 + 1 + num_classes] (unscaled offsets, obj_score, class_probs)
        targets: [B, max_targets, 5] in (x1, y1, x2, y2, cls_id)
        """
        device = predictions.device
        batch_size, num_anchors, _ = predictions.shape
        grid, stride = self._generate_grids_and_strides(img_size[0], img_size[1], device)

        # Decode predicted boxes: (x1, y1, x2, y2)
        pred_xy = (predictions[..., :2] + grid) * stride
        pred_wh = torch.exp(predictions[..., 2:4].clamp(-20, 20)) * stride
        pred_x1y1 = pred_xy - pred_wh / 2
        pred_x2y2 = pred_xy + pred_wh / 2
        pred_boxes = torch.cat([pred_x1y1, pred_x2y2], dim=-1)

        pred_obj = predictions[..., 4]
        pred_cls = predictions[..., 5:]

        total_loss_iou = torch.tensor(0.0, device=device)
        total_loss_cls = torch.tensor(0.0, device=device)
        total_loss_obj = torch.tensor(0.0, device=device)
        total_pos = 0

        # Anchor centers in image coordinates
        anchor_centers = (grid + 0.5) * stride  # [1, num_anchors, 2]

        for b in range(batch_size):
            b_targets = targets[b]
            # Valid ground truths have width > 0
            valid_mask = (b_targets[:, 2] > b_targets[:, 0]) & (b_targets[:, 3] > b_targets[:, 1])
            gt_boxes = b_targets[valid_mask, :4]
            gt_classes = b_targets[valid_mask, 4].long()

            b_pred_boxes = pred_boxes[b]  # [num_anchors, 4]
            b_pred_obj = pred_obj[b]      # [num_anchors]
            b_pred_cls = pred_cls[b]      # [num_anchors, num_classes]

            if len(gt_boxes) == 0:
                # No objects in image: purely background objectness loss
                loss_obj = self.bce_loss(b_pred_obj, torch.zeros_like(b_pred_obj)).sum()
                total_loss_obj = total_loss_obj + loss_obj
                continue

            # Center sampling: match anchor centers within GT boxes
            # gt_boxes: [N_gt, 4], anchor_centers: [1, N_a, 2]
            ac_x = anchor_centers[0, :, 0:1].T  # [1, N_a]
            ac_y = anchor_centers[0, :, 1:2].T  # [1, N_a]

            in_box_l = ac_x - gt_boxes[:, 0:1]  # [N_gt, N_a]
            in_box_r = gt_boxes[:, 2:3] - ac_x
            in_box_t = ac_y - gt_boxes[:, 1:2]
            in_box_b = gt_boxes[:, 3:4] - ac_y

            in_box_mask = (in_box_l > 0) & (in_box_r > 0) & (in_box_t > 0) & (in_box_b > 0)  # [N_gt, N_a]
            pos_anchor_mask = in_box_mask.any(dim=0)  # [N_a]

            if not pos_anchor_mask.any():
                # Fallback: find closest anchor for each GT box
                gt_centers = (gt_boxes[:, :2] + gt_boxes[:, 2:]) / 2
                dists = torch.cdist(gt_centers, anchor_centers[0])
                closest_idx = dists.argmin(dim=1)
                pos_anchor_mask[closest_idx] = True

            # Match each positive anchor to closest GT box
            matched_gt_idx = in_box_mask.float()[:, pos_anchor_mask].argmax(dim=0)
            matched_gt_boxes = gt_boxes[matched_gt_idx]
            matched_gt_classes = gt_classes[matched_gt_idx]

            matched_pred_boxes = b_pred_boxes[pos_anchor_mask]
            matched_pred_cls = b_pred_cls[pos_anchor_mask]

            num_pos = pos_anchor_mask.sum().item()
            total_pos += num_pos

            # Regression loss
            loss_iou = self.iou_loss(matched_pred_boxes, matched_gt_boxes).sum()
            total_loss_iou = total_loss_iou + loss_iou

            # Classification loss (One-hot BCE with logits)
            cls_targets = F.one_hot(matched_gt_classes, num_classes=self.num_classes).float()
            loss_cls = self.bce_loss(matched_pred_cls, cls_targets).sum()
            total_loss_cls = total_loss_cls + loss_cls

            # Objectness loss (BCE with logits)
            obj_targets = torch.zeros_like(b_pred_obj)
            obj_targets[pos_anchor_mask] = 1.0
            loss_obj = self.bce_loss(b_pred_obj, obj_targets).sum()
            total_loss_obj = total_loss_obj + loss_obj

        num_pos_norm = max(total_pos, 1)
        loss_iou = (total_loss_iou / num_pos_norm) * self.reg_weight
        loss_cls = (total_loss_cls / num_pos_norm) * self.cls_weight
        loss_obj = (total_loss_obj / num_pos_norm) * self.obj_weight

        total_loss = loss_iou + loss_cls + loss_obj

        loss_metrics = {
            "loss_total": float(total_loss.detach()),
            "loss_iou": float(loss_iou.detach()),
            "loss_cls": float(loss_cls.detach()),
            "loss_obj": float(loss_obj.detach()),
            "matched_positives": total_pos,
        }

        return total_loss, loss_metrics
