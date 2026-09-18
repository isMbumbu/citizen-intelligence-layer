"""Application functions for the narrow citizen issue-reporting flow."""

from collections.abc import Callable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.civic_action import repository
from app.api.v1.modules.civic_action.schemas import (
    CitizenReportCreateRequest,
    CitizenReportDetailResponse,
    CitizenReportResponse,
    CitizenReportStatusHistoryResponse,
    InstitutionResponseResponse,
    ReportingChannelResponse,
    ReportInstitutionResponse,
)
from app.api.v1.modules.geography import repository as geography_repository
from app.api.v1.modules.projects import repository as projects_repository
from app.core.logging import logger
from app.models.enums import (
    ReportCategory,
    ReportInstitutionRelationship,
    ReportStatus,
)
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
    InstitutionResponse,
    ReportingChannel,
    ReportInstitutionLink,
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


async def link_report_to_institution(
    session: AsyncSession,
    report_id: UUID,
    institution_id: UUID,
    relationship_type: ReportInstitutionRelationship,
) -> ReportInstitutionLink:
    """Create one internal report-institution relationship without status changes."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Institution link report was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    institution = await repository.get_institution(session, institution_id)
    if institution is None:
        logger.info("Institution link target was not found id=%s", institution_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found.",
        )
    if not institution.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Institution is inactive.",
        )
    existing = await repository.get_report_institution_link(
        session,
        report_id,
        institution_id,
        relationship_type.value,
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is already linked to this institution.",
        )
    link = ReportInstitutionLink(
        report_id=report_id,
        institution_id=institution_id,
        relationship_type=relationship_type,
    )
    try:
        return await repository.create_report_institution_link(session, link)
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is already linked to this institution.",
        ) from error


async def get_report_institutions(
    session: AsyncSession,
    report_id: UUID,
) -> list[ReportInstitutionResponse]:
    """Return public-safe institution relationships for one report."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Report institution lookup target was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    relationships = await repository.list_report_institution_links(session, report_id)
    relationships.sort(key=lambda item: (item[0].created_at, str(item[0].id)))
    return [
        ReportInstitutionResponse(
            institution_id=institution.id,
            institution_name=institution.name,
            institution_role=institution.role,
            relationship_type=link.relationship_type,
        )
        for link, institution in relationships
    ]


async def create_institution_response(
    session: AsyncSession,
    report_id: UUID,
    institution_id: UUID,
    content: str,
) -> InstitutionResponse:
    """Create one internal response through an existing active institution link."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Institution response report was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    institution = await repository.get_institution(session, institution_id)
    if institution is None:
        logger.info(
            "Institution response institution was not found id=%s", institution_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found.",
        )
    link = await repository.get_report_institution_link_for_response(
        session,
        report_id,
        institution_id,
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Institution is not linked to this report.",
        )
    if not institution.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Institution is inactive.",
        )
    try:
        response = InstitutionResponse(
            report_institution_link_id=link.id,
            content=content,
        )
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The institution response is invalid.",
        ) from error
    return await repository.create_institution_response(session, response)


async def get_report_responses(
    session: AsyncSession,
    report_id: UUID,
) -> list[InstitutionResponseResponse]:
    """Return public-safe institution responses for one report."""
    report = await repository.get(session, report_id)
    if report is None:
        logger.info("Institution response lookup target was not found id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    responses = await repository.list_institution_responses(session, report_id)
    responses.sort(key=lambda item: (item[0].created_at, str(item[0].id)))
    return [
        InstitutionResponseResponse(
            response_id=response.id,
            institution_id=institution.id,
            institution_name=institution.name,
            institution_role=institution.role,
            relationship_type=link.relationship_type,
            content=response.content,
            created_at=response.created_at,
        )
        for response, link, institution in responses
    ]


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
            if channel.is_active and matches_geography(channel)
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
