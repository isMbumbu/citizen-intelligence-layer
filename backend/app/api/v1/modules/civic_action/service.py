"""Application functions for the narrow citizen issue-reporting flow."""

from collections.abc import Callable
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.civic_action import repository
from app.api.v1.modules.civic_action.schemas import (
    CitizenReportCreateRequest,
    CitizenReportDetailResponse,
    CitizenReportResponse,
    CitizenReportStatusHistoryResponse,
    ReportingChannelResponse,
)
from app.api.v1.modules.geography import repository as geography_repository
from app.api.v1.modules.projects import repository as projects_repository
from app.core.logging import logger
from app.models.enums import ReportCategory, ReportStatus
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
    ReportingChannel,
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


async def get_report_channels(
    session: AsyncSession,
    report_id: UUID,
) -> list[ReportingChannelResponse]:
    """Return the most specific active reporting channels for one report."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Report channel lookup target was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    project = await projects_repository.get(session, report.project_id)
    if project is None:
        logger.info("Report channel project was not found id=%s", report.project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    location = await geography_repository.get_location_for_ward(
        session, project.ward_id
    )
    if location is None:
        logger.info("Report channel project location was not found id=%s", project.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project location not found.",
        )
    county, sub_county, ward = location
    channels = await repository.list_matching_channels(
        session,
        report.category,
        county.id,
        sub_county.id,
        ward.id,
    )
    channels = [
        channel
        for channel in channels
        if channel.is_active and channel.issue_category == report.category
    ]
    selected = _most_specific_channels(channels, ward.id, sub_county.id, county.id)
    return [_channel_response(channel) for channel in selected]


def _most_specific_channels(
    channels: list[ReportingChannel],
    ward_id: UUID,
    sub_county_id: UUID,
    county_id: UUID,
) -> list[ReportingChannel]:
    """Select one geography level and order its channels deterministically."""
    geography_matches: tuple[Callable[[ReportingChannel], bool], ...] = (
        lambda channel: channel.ward_id == ward_id,
        lambda channel: channel.sub_county_id == sub_county_id,
        lambda channel: channel.county_id == county_id,
    )
    for matches_geography in geography_matches:
        matching = [
            channel
            for channel in channels
            if channel.is_active
            and matches_geography(channel)
        ]
        if matching:
            return sorted(
                matching,
                key=lambda channel: (channel.priority, str(channel.id)),
            )
    return []


def _channel_response(channel: ReportingChannel) -> ReportingChannelResponse:
    """Convert one reporting channel to its public API contract."""
    return ReportingChannelResponse(
        id=channel.id,
        office_name=channel.office_name,
        channel_type=channel.channel_type,
        destination=channel.destination,
        display_label=channel.display_label,
        priority=channel.priority,
    )
