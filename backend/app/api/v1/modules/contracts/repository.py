"""Asynchronous SQLModel queries for project contract details."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vertical_slice import Contractor, ProjectContract


async def get_current_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> tuple[ProjectContract, Contractor] | None:
    """Return the latest contract and its contractor identity for a project."""
    result = await session.exec(
        select(ProjectContract)
        .where(ProjectContract.project_id == project_id)
        .order_by(ProjectContract.created_at.desc())
        .limit(1)
    )
    contract = result.first()
    if contract is None:
        return None
    contractor = await session.get(Contractor, contract.contractor_id)
    if contractor is None:
        return None
    return contract, contractor
