"""Asynchronous SQLModel queries for project verification records."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vertical_slice import ProjectVerification


async def get_latest_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> ProjectVerification | None:
    """Return the latest explicitly recorded verification state."""
    result = await session.exec(
        select(ProjectVerification)
        .where(ProjectVerification.project_id == project_id)
        .order_by(col(ProjectVerification.recorded_at).desc())
        .limit(1)
    )
    return result.first()
