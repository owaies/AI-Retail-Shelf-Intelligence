from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Retail Vision Intelligence API"
    database_url: str | None = Field(default=None, repr=False)
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret_key: str | None = Field(default=None, repr=False)
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "retail-shelf-intelligence"
    model_url: str = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_tiny.onnx"
    model_path: str = ".cache/models/yolox_tiny.onnx"
    model_input_size: int = 416
    detection_confidence: float = 0.25
    nms_iou_threshold: float = 0.45
    max_model_bytes: int = 80 * 1024 * 1024
    max_upload_bytes: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
