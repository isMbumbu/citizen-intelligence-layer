"""Focused tests for the asynchronous infrastructure readiness service."""

from unittest.mock import AsyncMock

from sqlalchemy.exc import OperationalError

from app.core import readiness
from app.core.readiness import DependencyStatus


async def test_readiness_checks_postgresql_and_redis_independently(
    monkeypatch,
) -> None:
    """Redis is checked even when PostgreSQL is unavailable."""
    session = AsyncMock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception())
    ping = AsyncMock(return_value=True)
    monkeypatch.setattr(readiness.redis_client, "ping", ping)

    report = await readiness.get_readiness_report(session)

    assert report.status == "not_ready"
    assert report.dependencies.postgresql is DependencyStatus.UNAVAILABLE
    assert report.dependencies.redis is DependencyStatus.READY
    session.execute.assert_awaited_once()
    ping.assert_awaited_once()
