from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_analysis_endpoint_requires_authentication() -> None:
    response = client.get("/api/analyses")
    assert response.status_code == 401


def test_oversized_request_is_rejected_before_multipart_processing() -> None:
    payload = b"x" * (settings.max_request_body_bytes + 1)
    response = client.post(
        "/api/analyses",
        content=payload,
        headers={"content-type": "application/octet-stream"},
    )
    assert response.status_code == 413
