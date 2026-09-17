from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok() -> None:
    """The liveness route remains independent from infrastructure availability."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_documents_health_endpoint() -> None:
    """Interactive API documentation has a registered liveness route."""
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
