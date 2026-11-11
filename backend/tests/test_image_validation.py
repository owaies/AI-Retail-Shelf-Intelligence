from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app.utils.image_validation import safe_filename, validate_image_upload


def _image_bytes(image_format: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(buffer, format=image_format)
    return buffer.getvalue()


JPEG = _image_bytes("JPEG")
PNG = _image_bytes("PNG")
WEBP = _image_bytes("WEBP")


def test_valid_jpeg_upload() -> None:
    validate_image_upload("shelf.jpg", "image/jpeg", JPEG)


@pytest.mark.parametrize(
    "filename, content_type, data",
    [
        ("shelf.exe", "image/jpeg", JPEG),
        ("shelf.jpg", "application/octet-stream", JPEG),
        ("shelf.png", "image/jpeg", JPEG),
        ("shelf.jpg", "image/png", PNG),
        ("shelf.jpg", "image/jpeg", PNG),
        ("shelf.jpg", "image/jpeg", b"not-an-image"),
        ("shelf.jpg", "image/jpeg", b"\\xff\\xd8\\xffnot-a-valid-jpeg"),
        ("shelf.jpg", "image/jpeg", b"x" * (10 * 1024 * 1024 + 1)),
    ],
    ids=[
        "invalid_extension",
        "invalid_content_type",
        "extension_mime_mismatch_jpeg_png",
        "extension_mime_mismatch_png_jpeg",
        "signature_mismatch",
        "corrupt_data",
        "invalid_jpeg_after_signature",
        "oversized_payload",
    ],
)
def test_invalid_uploads_are_rejected(filename: str, content_type: str, data: bytes) -> None:
    with pytest.raises(ValueError):
        validate_image_upload(filename, content_type, data)


def test_webp_signature_is_supported() -> None:
    validate_image_upload("shelf.webp", "image/webp", WEBP)


def test_rejects_oversized_decoded_image_before_pixel_verification(monkeypatch) -> None:
    class OversizedImage:
        format = "JPEG"
        size = (8_000, 6_000)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def verify(self):
            pytest.fail("oversized image must be rejected before pixel verification")

    monkeypatch.setattr("app.utils.image_validation.Image.open", lambda *_args: OversizedImage())

    with pytest.raises(ValueError, match="40 megapixels"):
        validate_image_upload("shelf.jpg", "image/jpeg", JPEG)


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("C:\\Users\\person\\shelf.png", "shelf.png"),
        ("../../etc/passwd", "passwd"),
        ("..\\..\\secrets.txt", "secrets.txt"),
        ("", "image"),
        (None, "image"),
    ],
)
def test_safe_filename_strips_cross_platform_path_components(filename, expected) -> None:
    assert safe_filename(filename) == expected


def test_safe_filename_limits_display_name_length() -> None:
    assert len(safe_filename("a" * 300 + ".png")) == 255


def test_custom_upload_limit_accepts_exact_boundary() -> None:
    validate_image_upload("shelf.jpg", "image/jpeg", JPEG, max_bytes=len(JPEG))


def test_custom_upload_limit_rejects_payload_above_boundary() -> None:
    with pytest.raises(ValueError, match=f"between 1 byte and {len(JPEG) - 1} bytes"):
        validate_image_upload("shelf.jpg", "image/jpeg", JPEG, max_bytes=len(JPEG) - 1)


def test_custom_upload_limit_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive number"):
        validate_image_upload("shelf.jpg", "image/jpeg", JPEG, max_bytes=0)
