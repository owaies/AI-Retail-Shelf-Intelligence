from __future__ import annotations

from pathlib import Path

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSION_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAGIC = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
}


def validate_image_upload(filename: str | None, content_type: str | None, data: bytes) -> None:
    extension = Path(filename or "").suffix.lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported image MIME type. Use JPEG, PNG or WebP.")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported image extension. Use .jpg, .jpeg, .png or .webp.")
    if EXTENSION_MIME_TYPES[extension] != content_type:
        raise ValueError("Image extension does not match the declared MIME type.")
    if len(data) <= 0 or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image must be between 1 byte and 10 MB.")
    if not MAGIC[content_type](data[:32]):
        raise ValueError("Image content does not match the declared MIME type.")


def safe_filename(filename: str | None) -> str:
    """Return a safe display name; never use it as a filesystem path."""
    # Browser uploads can contain Windows separators even when the server runs
    # on POSIX, so normalize both separator styles before taking the basename.
    normalized = (filename or "image").replace("\\", "/")
    name = Path(normalized).name.replace("..", "_")
    return name[:255] or "image"
