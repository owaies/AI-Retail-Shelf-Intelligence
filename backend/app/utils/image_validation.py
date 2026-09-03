from pathlib import Path

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def validate_image_metadata(filename: str | None, content_type: str | None, size: int) -> None:
    extension = Path(filename or "").suffix.lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported image MIME type.")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported image extension.")
    if size <= 0 or size > MAX_IMAGE_BYTES:
        raise ValueError("Image must be between 1 byte and 10 MB.")


def safe_filename(filename: str | None) -> str:
    """Return a filesystem-safe display name; never use it as a storage path."""
    return Path(filename or "image").name.replace("..", "_")
