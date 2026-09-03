from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreparedImage:
    path: Path
    width: int
    height: int


class ImageProcessor:
    """Boundary for OpenCV preprocessing, intentionally unimplemented on Day 1."""

    def prepare(self, image_path: Path) -> PreparedImage:
        raise NotImplementedError("OpenCV preprocessing is scheduled for Day 2.")
