from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.main as main
from app.core.database import get_session
from app.core.readiness import DependencyReadiness, DependencyStatus, ReadinessReport
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


def test_readiness_check_reports_each_required_dependency(
    monkeypatch,
) -> None:
    """Readiness distinguishes PostgreSQL and Redis without exposing settings."""

    async def override_get_session():
        yield AsyncMock()

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(
        main,
        "get_readiness_report",
        AsyncMock(
            return_value=ReadinessReport(
                status="ready",
                dependencies=DependencyReadiness(
                    postgresql=DependencyStatus.READY,
                    redis=DependencyStatus.READY,
                ),
            )
        ),
    )
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {"postgresql": "ready", "redis": "ready"},
    }


def test_readiness_check_reports_unavailable_dependency(
    monkeypatch,
) -> None:
    """A failed dependency produces a stable, non-sensitive readiness response."""

    async def override_get_session():
        yield AsyncMock()

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(
        main,
        "get_readiness_report",
        AsyncMock(
            return_value=ReadinessReport(
                status="not_ready",
                dependencies=DependencyReadiness(
                    postgresql=DependencyStatus.UNAVAILABLE,
                    redis=DependencyStatus.READY,
                ),
            )
        ),
    )
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "status": "not_ready",
            "dependencies": {"postgresql": "unavailable", "redis": "ready"},
        }
    }
