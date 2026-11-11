from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSION_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
PIL_FORMATS = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAGIC = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
}


def validate_image_upload(
    filename: str | None,
    content_type: str | None,
    data: bytes,
    *,
    max_bytes: int = MAX_IMAGE_BYTES,
) -> None:
    if max_bytes < 1:
        raise ValueError("Image upload limit must be a positive number of bytes.")

    extension = Path(filename or "").suffix.lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported image MIME type. Use JPEG, PNG or WebP.")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported image extension. Use .jpg, .jpeg, .png or .webp.")
    if EXTENSION_MIME_TYPES[extension] != content_type:
        raise ValueError("Image extension does not match the declared MIME type.")
    if len(data) <= 0 or len(data) > max_bytes:
        raise ValueError(f"Image must be between 1 byte and {max_bytes} bytes.")
    if not MAGIC[content_type](data[:32]):
        raise ValueError("Image content does not match the declared MIME type.")

    # Inspect image headers before OpenCV decodes pixels. A small compressed
    # upload can expand into a very large image and exhaust inference memory.
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != PIL_FORMATS[content_type]:
                raise ValueError("Image content does not match the declared MIME type.")
            width, height = image.size
            if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions must not exceed 40 megapixels.")
            image.verify()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Image content is not a valid supported image.") from exc


def safe_filename(filename: str | None) -> str:
    """Return a safe display name; never use it as a filesystem path."""
    # Browser uploads can contain Windows separators even when the server runs
    # on POSIX, so normalize both separator styles before taking the basename.
    normalized = (filename or "image").replace("\\", "/")
    name = Path(normalized).name.replace("..", "_")
    return name[:255] or "image"
