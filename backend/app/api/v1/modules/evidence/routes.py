"""Thin HTTP routes for evidence metadata."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.evidence import service
from app.api.v1.modules.evidence.schemas import EvidenceCreateRequest, EvidenceResponse
from app.core.database import get_session

router = APIRouter(tags=["evidence"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/projects/{project_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_evidence(
    project_id: UUID,
    payload: EvidenceCreateRequest,
    session: SessionDep,
) -> EvidenceResponse:
    """Create citizen evidence metadata for a project or its comment."""
    return await service.create_project_evidence(session, project_id, payload)


@router.post(
    "/projects/{project_id}/reports/{report_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report_evidence(
    project_id: UUID,
    report_id: UUID,
    payload: EvidenceCreateRequest,
    session: SessionDep,
) -> EvidenceResponse:
    """Create citizen evidence metadata for an issue report."""
    return await service.create_report_evidence(
        session,
        project_id,
        report_id,
        payload,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: UUID,
    session: SessionDep,
) -> EvidenceResponse:
    """Return evidence metadata without retrieving uploaded file content."""
    return await service.get_evidence(session, evidence_id)
