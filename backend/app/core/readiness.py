"""Asynchronous infrastructure readiness checks for the API process."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.core.redis import redis_client


class DependencyStatus(StrEnum):
    """Public, non-sensitive dependency states used by readiness responses."""

    READY = "ready"
    UNAVAILABLE = "unavailable"


class DependencyReadiness(BaseModel):
    """Readiness states for the infrastructure required to serve requests."""

    postgresql: DependencyStatus
    redis: DependencyStatus


class ReadinessReport(BaseModel):
    """A stable health contract that never exposes connection details."""

    status: Literal["ready", "not_ready"]
    dependencies: DependencyReadiness


async def get_readiness_report(session: AsyncSession) -> ReadinessReport:
    """Check PostgreSQL and Redis independently so failures remain diagnosable."""
    postgresql = await _check_postgresql(session)
    redis = await _check_redis()
    dependencies = DependencyReadiness(postgresql=postgresql, redis=redis)
    return ReadinessReport(
        status=(
            "ready"
            if all(
                dependency is DependencyStatus.READY
                for dependency in (postgresql, redis)
            )
            else "not_ready"
        ),
        dependencies=dependencies,
    )


async def _check_postgresql(session: AsyncSession) -> DependencyStatus:
    """Return PostgreSQL availability without leaking database configuration."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        _log_dependency_failure("postgresql", error)
        return DependencyStatus.UNAVAILABLE
    return DependencyStatus.READY


async def _check_redis() -> DependencyStatus:
    """Return Redis availability without leaking connection configuration."""
    try:
        await redis_client.ping()
    except RedisError as error:
        _log_dependency_failure("redis", error)
        return DependencyStatus.UNAVAILABLE
    return DependencyStatus.READY


def _log_dependency_failure(dependency: str, error: Exception) -> None:
    """Record operational context while deliberately omitting sensitive details."""
    logger.warning(
        "Readiness dependency unavailable",
        extra={
            "event": "readiness_dependency_unavailable",
            "dependency": dependency,
            "error_type": type(error).__name__,
        },
    )
