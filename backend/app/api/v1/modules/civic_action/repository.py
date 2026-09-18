"""Asynchronous SQLModel persistence functions for citizen issue reports."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
    Institution,
    InstitutionResponse,
    ReportingChannel,
    ReportInstitutionLink,
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


async def list_matching_channels(
    session: AsyncSession,
    issue_category: str,
    county_id: UUID,
    sub_county_id: UUID,
    ward_id: UUID,
) -> list[ReportingChannel]:
    """Return active category channels at any matching geography level."""
    result = await session.exec(
        select(ReportingChannel).where(
            ReportingChannel.issue_category == issue_category,
            col(ReportingChannel.is_active).is_(True),
            (
                (ReportingChannel.ward_id == ward_id)
                | (ReportingChannel.sub_county_id == sub_county_id)
                | (ReportingChannel.county_id == county_id)
            ),
        )
    )
    return list(result.all())


async def get_institution(
    session: AsyncSession,
    institution_id: UUID,
) -> Institution | None:
    """Return one institution reference record by identifier."""
    return await session.get(Institution, institution_id)


async def get_report_institution_link(
    session: AsyncSession,
    report_id: UUID,
    institution_id: UUID,
    relationship_type: str,
) -> ReportInstitutionLink | None:
    """Return an existing report-institution relationship, if present."""
    result = await session.exec(
        select(ReportInstitutionLink).where(
            ReportInstitutionLink.report_id == report_id,
            ReportInstitutionLink.institution_id == institution_id,
            ReportInstitutionLink.relationship_type == relationship_type,
        )
    )
    return result.first()


async def create_report_institution_link(
    session: AsyncSession,
    link: ReportInstitutionLink,
) -> ReportInstitutionLink:
    """Persist one report-institution relationship."""
    try:
        session.add(link)
        await session.commit()
        await session.refresh(link)
    except Exception:
        await session.rollback()
        logger.exception("Unable to link report to institution")
        raise
    return link


async def list_report_institution_links(
    session: AsyncSession,
    report_id: UUID,
) -> list[tuple[ReportInstitutionLink, Institution]]:
    """Return report institution relationships with public reference data."""
    result = await session.exec(
        select(ReportInstitutionLink, Institution)
        .join(Institution)
        .where(ReportInstitutionLink.report_id == report_id)
        .order_by(
            col(ReportInstitutionLink.created_at),
            col(ReportInstitutionLink.id),
        )
    )
    return list(result.all())


async def get_report_institution_link_for_response(
    session: AsyncSession,
    report_id: UUID,
    institution_id: UUID,
) -> ReportInstitutionLink | None:
    """Return the deterministic existing link eligible for one response."""
    result = await session.exec(
        select(ReportInstitutionLink)
        .where(
            ReportInstitutionLink.report_id == report_id,
            ReportInstitutionLink.institution_id == institution_id,
        )
        .order_by(
            col(ReportInstitutionLink.created_at),
            col(ReportInstitutionLink.id),
        )
        .limit(1)
    )
    return result.first()


async def create_institution_response(
    session: AsyncSession,
    response: InstitutionResponse,
) -> InstitutionResponse:
    """Persist one append-only institution response."""
    try:
        session.add(response)
        await session.commit()
        await session.refresh(response)
    except Exception:
        await session.rollback()
        logger.exception("Unable to store institution response")
        raise
    return response


async def list_institution_responses(
    session: AsyncSession,
    report_id: UUID,
) -> list[tuple[InstitutionResponse, ReportInstitutionLink, Institution]]:
    """Return report responses with their public institution relationship data."""
    result = await session.exec(
        select(InstitutionResponse, ReportInstitutionLink, Institution)
        .join(ReportInstitutionLink)
        .join(Institution)
        .where(ReportInstitutionLink.report_id == report_id)
        .order_by(
            col(InstitutionResponse.created_at),
            col(InstitutionResponse.id),
        )
    )
    return list(result.all())
