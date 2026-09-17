"""Thin HTTP routes for project browsing, evidence, verification, and review."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.projects import service
from app.api.v1.modules.projects.schemas import (
    ClaimEvidenceResponse,
    ProjectAnomalyResponse,
    ProjectDetailResponse,
    ProjectPageResponse,
    VerificationResponse,
)
from app.core.database import get_session
from app.models.enums import ProjectStatus, ProjectType

router = APIRouter(prefix="/projects", tags=["projects"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=ProjectPageResponse, summary="Browse projects")
async def list_projects(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    county: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    ward: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    project_type: ProjectType | None = None,
    status: ProjectStatus | None = None,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
) -> ProjectPageResponse:
    """Return a validated, paginated public-project browse result."""
    return await service.list_projects(
        session,
        county=county.strip() if county is not None else None,
        ward=ward.strip() if ward is not None else None,
        project_type=project_type,
        project_status=status,
        search=search.strip() if search is not None else None,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="View a project",
)
async def get_project(
    project_id: UUID,
    session: SessionDep,
) -> ProjectDetailResponse:
    """Return the project-page contract with important evidence references."""
    return await service.get_project_detail(session, project_id)


@router.get(
    "/{project_id}/sources",
    response_model=list[ClaimEvidenceResponse],
    summary="View project evidence",
)
async def get_project_sources(
    project_id: UUID,
    session: SessionDep,
) -> list[ClaimEvidenceResponse]:
    """Return material project claims and their source-record chains."""
    return await service.get_project_sources(session, project_id)


@router.get(
    "/{project_id}/verification",
    response_model=VerificationResponse | None,
    summary="View project verification state",
)
async def get_project_verification(
    project_id: UUID,
    session: SessionDep,
) -> VerificationResponse | None:
    """Expose explicit verification separately from derived review flags."""
    return await service.get_project_verification(session, project_id)


@router.get(
    "/{project_id}/anomalies",
    response_model=list[ProjectAnomalyResponse],
    summary="View evidence-grounded review flags",
)
async def get_project_anomalies(
    project_id: UUID,
    session: SessionDep,
) -> list[ProjectAnomalyResponse]:
    """Return deterministic review flags, never misconduct allegations."""
    return await service.get_project_anomalies(session, project_id)
