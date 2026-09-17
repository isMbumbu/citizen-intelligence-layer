"""Asynchronous SQLModel queries for project financial records."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vertical_slice import FinancialRecord


async def list_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> list[FinancialRecord]:
    """Return the current financial records for one project."""
    result = await session.exec(
        select(FinancialRecord)
        .where(FinancialRecord.project_id == project_id)
        .order_by(FinancialRecord.kind)
    )
    return list(result.all())
