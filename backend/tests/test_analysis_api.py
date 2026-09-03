from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analysis_endpoint_requires_authentication() -> None:
    response = client.get("/api/analyses")
    assert response.status_code == 401
