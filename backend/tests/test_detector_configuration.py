from app.core.config import settings
from app.services.vision import MODEL_NAME, MODEL_VERSION, VisionService


def test_production_detector_configuration_matches_yolox_s_baseline() -> None:
    service = VisionService()

    assert MODEL_NAME == "YOLOX-S"
    assert MODEL_VERSION == "0.1.1rc0"
    assert service.model_name == MODEL_NAME
    assert service.model_version == MODEL_VERSION
    assert service.processor.input_size == settings.model_input_size == 640
    assert settings.detection_confidence == 0.20
    assert settings.nms_iou_threshold == 0.45
    assert settings.model_url.endswith("/yolox_s.onnx")
    assert settings.model_path.endswith("/yolox_s.onnx") or settings.model_path.endswith("\\yolox_s.onnx")
