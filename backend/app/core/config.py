from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Retail Vision Intelligence API"
    database_url: str | None = Field(default=None, repr=False)
    database_schema: str = "retail_shelf_intelligence"
    supabase_url: str | None = Field(default=None, repr=False)
    supabase_publishable_key: str | None = Field(default=None, repr=False)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://ai-retail-shelf-intelligence.vercel.app",
        "https://ai-retail-shelf-intelligence-owaies-projects.vercel.app",
        "https://ai-retail-shelf-intelligence-git-main-owaies-projects.vercel.app",
    ]
    jwt_secret_key: str | None = Field(default=None, repr=False)
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "retail-shelf-intelligence"
    # Higher-capacity official YOLOX checkpoint. Still COCO-trained, so this is
    # an accuracy-oriented baseline upgrade, not a retail/SKU model.
    model_url: str = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.onnx"
    model_path: str = "/tmp/retail-shelf-intelligence/yolox_s.onnx"
    # Official YOLOX-S ONNX checkpoint is exported for a fixed 640x640 input.
    model_input_size: int = 640
    detection_confidence: float = 0.20
    nms_iou_threshold: float = 0.45
    max_model_bytes: int = 80 * 1024 * 1024
    max_upload_bytes: int = 10 * 1024 * 1024
    max_request_body_bytes: int = 12 * 1024 * 1024

    @field_validator("cors_origins")
    @classmethod
    def ensure_required_origins(cls, value: list[str]) -> list[str]:
        required = {
            "http://localhost:5173",
            "https://ai-retail-shelf-intelligence.vercel.app",
            "https://ai-retail-shelf-intelligence-owaies-projects.vercel.app",
            "https://ai-retail-shelf-intelligence-git-main-owaies-projects.vercel.app",
        }
        return list(dict.fromkeys([*value, *required]))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
