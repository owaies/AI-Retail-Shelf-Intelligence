import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("field", ["max_model_bytes", "max_upload_bytes", "max_request_body_bytes"])
def test_size_limits_must_be_positive(field: str) -> None:
    values = {
        "max_model_bytes": 1024,
        "max_upload_bytes": 1024,
        "max_request_body_bytes": 2048,
    }
    values[field] = 0

    with pytest.raises(ValidationError, match="positive integers"):
        Settings(_env_file=None, **values)


def test_request_body_limit_must_cover_configured_upload_limit() -> None:
    with pytest.raises(ValidationError, match="max_request_body_bytes"):
        Settings(
            _env_file=None,
            max_model_bytes=1024,
            max_upload_bytes=2048,
            max_request_body_bytes=1024,
        )


def test_valid_custom_media_limits_are_preserved() -> None:
    settings = Settings(
        _env_file=None,
        max_model_bytes=4096,
        max_upload_bytes=2048,
        max_request_body_bytes=3072,
    )

    assert settings.max_model_bytes == 4096
    assert settings.max_upload_bytes == 2048
    assert settings.max_request_body_bytes == 3072


@pytest.mark.parametrize("field", ["detection_confidence", "nms_iou_threshold"])
@pytest.mark.parametrize("value", [-0.01, 1.01, float("nan"), float("inf"), float("-inf")])
def test_detection_probability_thresholds_must_be_finite_and_bounded(field: str, value: float) -> None:
    with pytest.raises(ValidationError, match="Detection thresholds"):
        Settings(_env_file=None, **{field: value})


def test_detection_probability_threshold_boundaries_are_valid() -> None:
    settings = Settings(
        _env_file=None,
        detection_confidence=0.0,
        nms_iou_threshold=1.0,
    )

    assert settings.detection_confidence == 0.0
    assert settings.nms_iou_threshold == 1.0
