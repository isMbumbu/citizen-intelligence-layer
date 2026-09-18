"""Thin HTTP route for a citizen issue report submitted against a project."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.civic_action import service
from app.api.v1.modules.civic_action.schemas import (
    CitizenReportCreateRequest,
    CitizenReportDetailResponse,
    CitizenReportResponse,
    InstitutionResponseResponse,
    ReportingChannelResponse,
    ReportInstitutionResponse,
)
from app.core.database import get_session

router = APIRouter(prefix="/projects", tags=["citizen reports"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/{project_id}/reports",
    response_model=CitizenReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a citizen issue report",
)
async def submit_project_report(
    project_id: UUID,
    payload: CitizenReportCreateRequest,
    session: SessionDep,
) -> CitizenReportResponse:
    """Store a valid unauthenticated report for an existing project."""
    return await service.submit_report(session, project_id, payload)


report_router = APIRouter(prefix="/reports", tags=["citizen reports"])


@report_router.get(
    "/{report_id}",
    response_model=CitizenReportDetailResponse,
    summary="View a citizen report status",
)
async def get_report(
    report_id: UUID,
    session: SessionDep,
) -> CitizenReportDetailResponse:
    """Return citizen-safe report status and lifecycle history."""
    return await service.get_report(session, report_id)


@report_router.get(
    "/{report_id}/channels",
    response_model=list[ReportingChannelResponse],
    summary="View reporting channels for a citizen report",
)
async def get_report_channels(
    report_id: UUID,
    session: SessionDep,
) -> list[ReportingChannelResponse]:
    """Return informational reporting channels without changing the report."""
    return await service.get_report_channels(session, report_id)


@report_router.get(
    "/{report_id}/institutions",
    response_model=list[ReportInstitutionResponse],
    summary="View institutions linked to a citizen report",
)
async def get_report_institutions(
    report_id: UUID,
    session: SessionDep,
) -> list[ReportInstitutionResponse]:
    """Return public-safe institution relationships for one report."""
    return await service.get_report_institutions(session, report_id)


@report_router.get(
    "/{report_id}/responses",
    response_model=list[InstitutionResponseResponse],
    summary="View institution responses for a citizen report",
)
async def get_report_responses(
    report_id: UUID,
    session: SessionDep,
) -> list[InstitutionResponseResponse]:
    """Return public-safe institution responses for one report."""
    return await service.get_report_responses(session, report_id)
