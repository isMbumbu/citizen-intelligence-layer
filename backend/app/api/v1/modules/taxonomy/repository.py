"""Asynchronous SQLModel queries for project taxonomy reference data."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vertical_slice import ProjectCategory, ProjectSubtype


async def list_active_categories(session: AsyncSession) -> list[ProjectCategory]:
    """Return public project categories in a stable display order."""
    result = await session.exec(
        select(ProjectCategory)
        .where(col(ProjectCategory.is_active).is_(True))
        .order_by(col(ProjectCategory.name))
    )
    return list(result.all())


async def list_active_subtypes(
    session: AsyncSession,
    category_ids: set[UUID],
) -> list[ProjectSubtype]:
    """Return active subtypes for the supplied active categories."""
    if not category_ids:
        return []
    result = await session.exec(
        select(ProjectSubtype)
        .where(
            col(ProjectSubtype.category_id).in_(category_ids),
            col(ProjectSubtype.is_active).is_(True),
        )
        .order_by(col(ProjectSubtype.name))
    )
    return list(result.all())


async def get_active_category(
    session: AsyncSession,
    category_id: UUID,
) -> ProjectCategory | None:
    """Return one active category, or no result for an inactive/unknown record."""
    result = await session.exec(
        select(ProjectCategory).where(
            ProjectCategory.id == category_id,
            col(ProjectCategory.is_active).is_(True),
        )
    )
    return result.first()
