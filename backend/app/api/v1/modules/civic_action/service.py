"""Application functions for the narrow citizen issue-reporting flow."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.civic_action import repository
from app.api.v1.modules.civic_action.schemas import (
    CitizenReportCreateRequest,
    CitizenReportDetailResponse,
    CitizenReportResponse,
    CitizenReportStatusHistoryResponse,
)
from app.api.v1.modules.projects import repository as projects_repository
from app.core.logging import logger
from app.models.enums import ReportCategory, ReportStatus
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
)

_REPORT_TRANSITIONS: dict[ReportStatus, ReportStatus] = {
    ReportStatus.SUBMITTED: ReportStatus.UNDER_REVIEW,
    ReportStatus.UNDER_REVIEW: ReportStatus.REFERRED,
    ReportStatus.REFERRED: ReportStatus.RESPONDED,
    ReportStatus.RESPONDED: ReportStatus.RESOLVED,
    ReportStatus.RESOLVED: ReportStatus.CLOSED,
}


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
        category=ReportCategory(report.category),
        status=ReportStatus(report.status),
        submitted_at=report.submitted_at,
    )


async def get_report(
    session: AsyncSession,
    report_id: UUID,
) -> CitizenReportDetailResponse:
    """Return the citizen-safe report status and transition history."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Report was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    history = await repository.list_status_history(session, report_id)
    return CitizenReportDetailResponse(
        id=report.id,
        project_id=report.project_id,
        category=ReportCategory(report.category),
        status=ReportStatus(report.status),
        submitted_at=report.submitted_at,
        status_history=[
            CitizenReportStatusHistoryResponse(
                from_status=ReportStatus(item.from_status),
                to_status=ReportStatus(item.to_status),
                created_at=item.created_at,
            )
            for item in history
        ],
    )


async def transition_report_status(
    session: AsyncSession,
    report_id: UUID,
    to_status: ReportStatus,
) -> CitizenReportResponse:
    """Apply the single next status transition and audit it."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Report status transition target was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    current_status = ReportStatus(report.status)
    if _REPORT_TRANSITIONS.get(current_status) is not to_status:
        logger.info(
            "Rejected report status transition id=%s from=%s to=%s",
            report_id,
            current_status,
            to_status,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid report status transition.",
        )
    report.status = to_status.value
    try:
        report = await repository.update_status(
            session,
            report,
            CitizenReportStatusTransition(
                report_id=report.id,
                from_status=current_status.value,
                to_status=to_status.value,
            ),
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update report status.",
        ) from error
    return CitizenReportResponse(
        id=report.id,
        project_id=report.project_id,
        category=ReportCategory(report.category),
        status=ReportStatus(report.status),
        submitted_at=report.submitted_at,
    )
