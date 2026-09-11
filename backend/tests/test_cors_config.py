import json

from app.core.config import Settings


def test_required_frontend_origins_survive_environment_override(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        json.dumps(["https://example.com"]),
    )

    configured = Settings()

    assert "https://example.com" in configured.cors_origins
    assert "http://localhost:5173" in configured.cors_origins
    assert "https://ai-retail-shelf-intelligence.vercel.app" in configured.cors_origins
