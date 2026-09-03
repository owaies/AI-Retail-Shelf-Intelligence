from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Retail Vision Intelligence API"
    database_url: str | None = Field(default=None, repr=False)
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
