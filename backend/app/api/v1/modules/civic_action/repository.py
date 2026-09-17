"""Asynchronous SQLModel persistence functions for citizen issue reports."""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.vertical_slice import CitizenIssueReport


async def create(
    session: AsyncSession,
    report: CitizenIssueReport,
) -> CitizenIssueReport:
    """Persist one report without logging the citizen's message or contact data."""
    try:
        session.add(report)
        await session.commit()
        await session.refresh(report)
    except Exception:
        await session.rollback()
        logger.exception("Unable to store citizen report")
        raise
    logger.info(
        "Stored citizen report id=%s project_id=%s", report.id, report.project_id
    )
    return report
