"""Asynchronous SQLModel persistence functions for citizen issue reports."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
)


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


async def get(
    session: AsyncSession,
    report_id: UUID,
) -> CitizenIssueReport | None:
    """Return one citizen issue report by identifier."""
    return await session.get(CitizenIssueReport, report_id)


async def list_status_history(
    session: AsyncSession,
    report_id: UUID,
) -> list[CitizenReportStatusTransition]:
    """Return report transitions in deterministic chronological order."""
    result = await session.exec(
        select(CitizenReportStatusTransition)
        .where(CitizenReportStatusTransition.report_id == report_id)
        .order_by(
            col(CitizenReportStatusTransition.created_at),
            col(CitizenReportStatusTransition.id),
        )
    )
    return list(result.all())


async def update_status(
    session: AsyncSession,
    report: CitizenIssueReport,
    transition: CitizenReportStatusTransition,
) -> CitizenIssueReport:
    """Persist one report status and its audit record atomically."""
    try:
        session.add(report)
        session.add(transition)
        await session.commit()
        await session.refresh(report)
    except Exception:
        await session.rollback()
        logger.exception("Unable to update citizen report status")
        raise
    logger.info("Updated citizen report status id=%s", report.id)
    return report
