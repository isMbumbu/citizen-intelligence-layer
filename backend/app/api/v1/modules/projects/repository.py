"""Asynchronous SQLModel persistence functions for public-project browsing."""

from typing import Any
from uuid import UUID

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.enums import ProjectStatus
from app.models.vertical_slice import County, Project, ProjectProgress, SubCounty, Ward


async def list_projects(
    session: AsyncSession,
    *,
    county: str | None,
    ward: str | None,
    project_type: str | None,
    status: ProjectStatus | None,
    search: str | None,
    offset: int,
    limit: int,
) -> tuple[list[Project], int]:
    """Return one filtered project page and its full matching count."""
    conditions: list[Any] = []
    if county is not None:
        conditions.append(func.lower(County.name) == county.casefold())
    if ward is not None:
        conditions.append(func.lower(Ward.name) == ward.casefold())
    if project_type is not None:
        conditions.append(Project.project_type == project_type)
    if status is not None:
        conditions.append(Project.status == status.value)
    if search is not None:
        pattern = f"%{search.casefold()}%"
        conditions.append(
            (func.lower(Project.name).like(pattern))
            | (func.lower(Project.description).like(pattern))
        )

    statement = select(Project).join(Ward).join(SubCounty).join(County)
    count_statement = (
        select(func.count())
        .select_from(Project)
        .join(Ward)
        .join(SubCounty)
        .join(County)
    )
    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count_result = await session.exec(count_statement)
    result = await session.exec(
        statement.order_by(Project.name).offset(offset).limit(limit)
    )
    return list(result.all()), count_result.one()


async def get(session: AsyncSession, project_id: UUID) -> Project | None:
    """Return a project by primary key."""
    return await session.get(Project, project_id)


async def get_latest_progress(
    session: AsyncSession,
    project_id: UUID,
) -> ProjectProgress | None:
    """Return the latest reported project progress update."""
    result = await session.exec(
        select(ProjectProgress)
        .where(ProjectProgress.project_id == project_id)
        .order_by(
            col(ProjectProgress.reported_at).desc(),
            col(ProjectProgress.created_at).desc(),
        )
        .limit(1)
    )
    return result.first()
