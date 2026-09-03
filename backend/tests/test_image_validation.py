import pytest

from app.utils.image_validation import validate_image_upload


JPEG = b"\xff\xd8\xff" + b"x" * 20
PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 20
WEBP = b"RIFF" + b"0000" + b"WEBP" + b"x" * 20


def test_valid_jpeg_upload() -> None:
    validate_image_upload("shelf.jpg", "image/jpeg", JPEG)


@pytest.mark.parametrize(
    "filename, content_type, data",
    [
        ("shelf.exe", "image/jpeg", JPEG),
        ("shelf.jpg", "application/octet-stream", JPEG),
        ("shelf.jpg", "image/jpeg", PNG),
        ("shelf.jpg", "image/jpeg", b"not-an-image"),
        ("shelf.jpg", "image/jpeg", b"x" * (10 * 1024 * 1024 + 1)),
    ],
)
def test_invalid_uploads_are_rejected(filename: str, content_type: str, data: bytes) -> None:
    with pytest.raises(ValueError):
        validate_image_upload(filename, content_type, data)


def test_webp_signature_is_supported() -> None:
    validate_image_upload("shelf.webp", "image/webp", WEBP)
