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
