"""Application functions for the narrow citizen issue-reporting flow."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.civic_action import repository
from app.api.v1.modules.civic_action.schemas import (
    CitizenReportCreateRequest,
    CitizenReportResponse,
)
from app.api.v1.modules.projects import repository as projects_repository
from app.core.logging import logger
from app.models.enums import ReportStatus
from app.models.vertical_slice import CitizenIssueReport


async def submit_report(
    session: AsyncSession,
    project_id: UUID,
    payload: CitizenReportCreateRequest,
) -> CitizenReportResponse:
    """Store a valid report for an existing project in its submitted state."""
    project = await projects_repository.get(session, project_id)
    if project is None:
        logger.info("Rejected report for unknown project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    if not payload.description.strip():
        logger.info("Rejected empty citizen report for project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The issue report is invalid.",
        )
    try:
        report = await repository.create(
            session,
            CitizenIssueReport(
                project_id=project_id,
                category=payload.category.value,
                description=payload.description,
                contact_information=payload.contact_information,
                status=ReportStatus.SUBMITTED.value,
            ),
        )
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception(
            "Unable to submit citizen report for project id=%s", project_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to submit issue report.",
        ) from error
    return CitizenReportResponse(
        id=report.id,
        project_id=report.project_id,
        category=report.category,
        status=report.status,
        submitted_at=report.submitted_at,
    )
