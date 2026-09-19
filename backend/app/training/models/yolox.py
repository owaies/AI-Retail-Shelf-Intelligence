from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence
import urllib.request

import torch
import torch.nn as nn


class SiLU(nn.Module):
    """Export-friendly SiLU activation function."""
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * torch.sigmoid(x)


class BaseConv(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        ksize: int = 1,
        stride: int = 1,
        groups: int = 1,
        bias: bool = False,
        act: str = "silu",
    ) -> None:
        super().__init__()
        pad = (ksize - 1) // 2
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=ksize,
            stride=stride,
            padding=pad,
            groups=groups,
            bias=bias,
        )
        self.bn = nn.BatchNorm2d(out_channels, eps=1e-3, momentum=0.03)
        self.act = SiLU() if act == "silu" else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.conv(x)))


class Focus(nn.Module):
    """Focus width and height information into channel space."""
    def __init__(self, in_channels: int, out_channels: int, ksize: int = 3, stride: int = 1, act: str = "silu") -> None:
        super().__init__()
        self.conv = BaseConv(in_channels * 4, out_channels, ksize, stride, act=act)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        patch_top_left = x[..., ::2, ::2]
        patch_top_right = x[..., ::2, 1::2]
        patch_bot_left = x[..., 1::2, ::2]
        patch_bot_right = x[..., 1::2, 1::2]
        x = torch.cat((patch_top_left, patch_bot_left, patch_top_right, patch_bot_right), dim=1)
        return self.conv(x)


class Bottleneck(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        shortcut: bool = True,
        expansion: float = 0.5,
        act: str = "silu",
    ) -> None:
        super().__init__()
        hidden_channels = int(out_channels * expansion)
        self.conv1 = BaseConv(in_channels, hidden_channels, 1, stride=1, act=act)
        self.conv2 = BaseConv(hidden_channels, out_channels, 3, stride=1, act=act)
        self.use_add = shortcut and in_channels == out_channels

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.conv2(self.conv1(x))
        return x + y if self.use_add else y


class SPPBottleneck(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_sizes: Sequence[int] = (5, 9, 13),
        act: str = "silu",
    ) -> None:
        super().__init__()
        hidden_channels = in_channels // 2
        self.conv1 = BaseConv(in_channels, hidden_channels, 1, stride=1, act=act)
        self.m = nn.ModuleList(
            [nn.MaxPool2d(kernel_size=ks, stride=1, padding=ks // 2) for ks in kernel_sizes]
        )
        self.conv2 = BaseConv(hidden_channels * (len(kernel_sizes) + 1), out_channels, 1, stride=1, act=act)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        return self.conv2(torch.cat([x] + [m(x) for m in self.m], dim=1))


class CSPLayer(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        n: int = 1,
        shortcut: bool = True,
        expansion: float = 0.5,
        act: str = "silu",
    ) -> None:
        super().__init__()
        hidden_channels = int(out_channels * expansion)
        self.conv1 = BaseConv(in_channels, hidden_channels, 1, stride=1, act=act)
        self.conv2 = BaseConv(in_channels, hidden_channels, 1, stride=1, act=act)
        self.conv3 = BaseConv(2 * hidden_channels, out_channels, 1, stride=1, act=act)
        module_list = [
            Bottleneck(hidden_channels, hidden_channels, shortcut=shortcut, expansion=1.0, act=act)
            for _ in range(n)
        ]
        self.m = nn.Sequential(*module_list)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_1 = self.conv1(x)
        x_2 = self.conv2(x)
        x_1 = self.m(x_1)
        x = torch.cat((x_1, x_2), dim=1)
        return self.conv3(x)


class CSPDarknet(nn.Module):
    def __init__(
        self,
        dep_mul: float = 0.33,
        wid_mul: float = 0.50,
        out_features: tuple[str, ...] = ("dark3", "dark4", "dark5"),
    ) -> None:
        super().__init__()
        self.out_features = out_features
        base_channels = int(wid_mul * 64)  # 32 for YOLOX-S
        base_depth = max(round(dep_mul * 3), 1)  # 1 for YOLOX-S

        # Stem: Focus layer
        self.stem = Focus(3, base_channels, ksize=3)

        # Dark2
        self.dark2 = nn.Sequential(
            BaseConv(base_channels, base_channels * 2, 3, 2),
            CSPLayer(base_channels * 2, base_channels * 2, n=base_depth),
        )

        # Dark3 (P3)
        self.dark3 = nn.Sequential(
            BaseConv(base_channels * 2, base_channels * 4, 3, 2),
            CSPLayer(base_channels * 4, base_channels * 4, n=base_depth * 3),
        )

        # Dark4 (P4)
        self.dark4 = nn.Sequential(
            BaseConv(base_channels * 4, base_channels * 8, 3, 2),
            CSPLayer(base_channels * 8, base_channels * 8, n=base_depth * 3),
        )

        # Dark5 (P5)
        self.dark5 = nn.Sequential(
            BaseConv(base_channels * 8, base_channels * 16, 3, 2),
            SPPBottleneck(base_channels * 16, base_channels * 16),
            CSPLayer(base_channels * 16, base_channels * 16, n=base_depth, shortcut=False),
        )

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        outputs = {}
        x = self.stem(x)
        x = self.dark2(x)
        x = self.dark3(x)
        outputs["dark3"] = x
        x = self.dark4(x)
        outputs["dark4"] = x
        x = self.dark5(x)
        outputs["dark5"] = x
        return {k: outputs[k] for k in self.out_features}


class YOLOPAFPN(nn.Module):
    def __init__(
        self,
        depth: float = 0.33,
        width: float = 0.50,
        in_features: tuple[str, ...] = ("dark3", "dark4", "dark5"),
        in_channels: tuple[int, ...] = (256, 512, 1024),
    ) -> None:
        super().__init__()
        self.backbone = CSPDarknet(depth, width, out_features=in_features)
        self.in_features = in_features

        in_channels = [int(c * width) for c in in_channels]  # [128, 256, 512] for YOLOX-S
        BaseConv_depth = max(round(depth * 3), 1)

        self.lateral_conv0 = BaseConv(in_channels[2], in_channels[1], 1, 1)
        self.C3_p4 = CSPLayer(in_channels[1] * 2, in_channels[1], n=BaseConv_depth, shortcut=False)
        self.reduce_conv1 = BaseConv(in_channels[1], in_channels[0], 1, 1)
        self.C3_p3 = CSPLayer(in_channels[0] * 2, in_channels[0], n=BaseConv_depth, shortcut=False)

        self.bu_conv2 = BaseConv(in_channels[0], in_channels[0], 3, 2)
        self.C3_n3 = CSPLayer(in_channels[0] * 2, in_channels[1], n=BaseConv_depth, shortcut=False)
        self.bu_conv1 = BaseConv(in_channels[1], in_channels[1], 3, 2)
        self.C3_n4 = CSPLayer(in_channels[1] * 2, in_channels[2], n=BaseConv_depth, shortcut=False)

    def forward(self, input: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        out_features = self.backbone(input)
        feat1 = out_features[self.in_features[0]]  # P3 / 128 ch
        feat2 = out_features[self.in_features[1]]  # P4 / 256 ch
        feat3 = out_features[self.in_features[2]]  # P5 / 512 ch

        # Top-down FPN
        p_5 = self.lateral_conv0(feat3)
        p_5_upsample = nn.functional.interpolate(p_5, scale_factor=2, mode="nearest")
        p_4 = torch.cat([p_5_upsample, feat2], dim=1)
        p_4 = self.C3_p4(p_4)

        p_4_reduce = self.reduce_conv1(p_4)
        p_4_upsample = nn.functional.interpolate(p_4_reduce, scale_factor=2, mode="nearest")
        p_3 = torch.cat([p_4_upsample, feat1], dim=1)
        p_3 = self.C3_p3(p_3)  # P3 out (128 ch)

        # Bottom-up PAN
        n_3_down = self.bu_conv2(p_3)
        n_3 = torch.cat([n_3_down, p_4_reduce], dim=1)
        n_3 = self.C3_n3(n_3)  # P4 out (256 ch)

        n_4_down = self.bu_conv1(n_3)
        n_4 = torch.cat([n_4_down, p_5], dim=1)
        n_4 = self.C3_n4(n_4)  # P5 out (512 ch)

        return p_3, n_3, n_4


class YOLOXHead(nn.Module):
    def __init__(
        self,
        num_classes: int = 80,
        width: float = 0.50,
        in_channels: tuple[int, ...] = (256, 512, 1024),
        strides: tuple[int, ...] = (8, 16, 32),
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.strides = strides
        in_channels = [int(c * width) for c in in_channels]  # [128, 256, 512] for YOLOX-S
        hidden_channels = int(256 * width)  # 128

        self.stems = nn.ModuleList([BaseConv(c, hidden_channels, 1, 1) for c in in_channels])
        self.cls_convs = nn.ModuleList([
            nn.Sequential(
                BaseConv(hidden_channels, hidden_channels, 3, 1),
                BaseConv(hidden_channels, hidden_channels, 3, 1),
            )
            for _ in in_channels
        ])
        self.reg_convs = nn.ModuleList([
            nn.Sequential(
                BaseConv(hidden_channels, hidden_channels, 3, 1),
                BaseConv(hidden_channels, hidden_channels, 3, 1),
            )
            for _ in in_channels
        ])
        self.cls_preds = nn.ModuleList([
            nn.Conv2d(hidden_channels, num_classes, kernel_size=1, stride=1, padding=0)
            for _ in in_channels
        ])
        self.reg_preds = nn.ModuleList([
            nn.Conv2d(hidden_channels, 4, kernel_size=1, stride=1, padding=0)
            for _ in in_channels
        ])
        self.obj_preds = nn.ModuleList([
            nn.Conv2d(hidden_channels, 1, kernel_size=1, stride=1, padding=0)
            for _ in in_channels
        ])

    def initialize_biases(self, prior_prob: float = 1e-2) -> None:
        for conv in self.cls_preds:
            b = conv.bias.view(1, -1)
            b.data.fill_(-math.log((1 - prior_prob) / prior_prob))
            conv.bias = torch.nn.Parameter(b.view(-1), requires_grad=True)

        for conv in self.obj_preds:
            b = conv.bias.view(1, -1)
            b.data.fill_(-math.log((1 - prior_prob) / prior_prob))
            conv.bias = torch.nn.Parameter(b.view(-1), requires_grad=True)

    def forward(self, xin: tuple[torch.Tensor, ...]) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
        outputs = []
        raw_outputs = []
        strides_list = []

        for k, (stride, x) in enumerate(zip(self.strides, xin)):
            x = self.stems[k](x)
            cls_feat = self.cls_convs[k](x)
            reg_feat = self.reg_convs[k](x)

            cls_output = self.cls_preds[k](cls_feat)
            reg_output = self.reg_preds[k](reg_feat)
            obj_output = self.obj_preds[k](reg_feat)

            # Shape: [B, 4 + 1 + num_classes, H, W]
            output = torch.cat([reg_output, obj_output.sigmoid(), cls_output.sigmoid()], dim=1)
            raw_output = torch.cat([reg_output, obj_output, cls_output], dim=1)
            strides_list.append(stride)

            # Flatten to [B, H*W, 4 + 1 + num_classes]
            b, c, h, w = output.shape
            output = output.view(b, c, -1).permute(0, 2, 1)
            raw_output = raw_output.view(b, c, -1).permute(0, 2, 1)
            outputs.append(output)
            raw_outputs.append(raw_output)

        return torch.cat(outputs, dim=1), torch.cat(raw_outputs, dim=1), strides_list


class YOLOX(nn.Module):
    """Exact YOLOX-S detector implementation with PAFPN backbone and Decoupled Head."""
    def __init__(self, backbone: YOLOPAFPN | None = None, head: YOLOXHead | None = None) -> None:
        super().__init__()
        self.backbone = backbone or YOLOPAFPN(depth=0.33, width=0.50)
        self.head = head or YOLOXHead(num_classes=80, width=0.50)

    def forward(self, x: torch.Tensor, return_raw: bool = False) -> torch.Tensor:
        fpn_outs = self.backbone(x)
        outputs, raw_outputs, _ = self.head(fpn_outs)
        if self.training or return_raw:
            return raw_outputs
        return outputs


def create_yolox_s(
    num_classes: int = 62,
    pretrained: bool = True,
    weights_path: Path | str | None = None,
    device: str | torch.device = "cpu",
) -> YOLOX:
    """Instantiate YOLOX-S with pretrained COCO weights and fine-tuning head adaptation."""
    backbone = YOLOPAFPN(depth=0.33, width=0.50)
    head = YOLOXHead(num_classes=num_classes, width=0.50)
    head.initialize_biases(prior_prob=1e-2)
    model = YOLOX(backbone=backbone, head=head)

    if pretrained:
        import tempfile
        default_dir = Path(tempfile.gettempdir()) / "retail-shelf-intelligence"
        ckpt_path = Path(weights_path) if weights_path else default_dir / "yolox_s.pth"
        if not ckpt_path.exists() or ckpt_path.stat().st_size == 0:
            ckpt_path.parent.mkdir(parents=True, exist_ok=True)
            url = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.pth"
            urllib.request.urlretrieve(url, ckpt_path)

        checkpoint = torch.load(str(ckpt_path), map_location="cpu")
        state_dict = checkpoint["model"] if "model" in checkpoint else checkpoint

        # Filter out classification prediction weights if num_classes doesn't match COCO (80)
        model_state = model.state_dict()
        matched_dict = {}
        for k, v in state_dict.items():
            if k in model_state:
                if model_state[k].shape == v.shape:
                    matched_dict[k] = v

        model_state.update(matched_dict)
        model.load_state_dict(model_state)

    model.to(device)
    return model
