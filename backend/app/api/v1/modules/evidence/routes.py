"""Thin HTTP routes for evidence metadata."""

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.evidence import service
from app.api.v1.modules.evidence.schemas import (
    EvidenceProcessingResponse,
    EvidenceResponse,
)
from app.core.database import get_session
from app.core.rate_limit import RateLimitOperation, enforce_rate_limit

router = APIRouter(tags=["evidence"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/comments/{comment_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment_evidence(
    comment_id: UUID,
    session: SessionDep,
    request: Request,
    uploader_id: UUID = Form(...),  # noqa: B008
    file: UploadFile = File(...),  # noqa: B008
) -> EvidenceResponse:
    """Validate and store one citizen evidence upload for a comment."""
    await enforce_rate_limit(
        request,
        operation=RateLimitOperation.UPLOAD,
        target_type="comment",
        target_id=comment_id,
    )
    return await service.upload_comment_evidence(session, comment_id, uploader_id, file)


@router.post(
    "/reports/{report_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report_evidence_by_id(
    report_id: UUID,
    session: SessionDep,
    request: Request,
    uploader_id: UUID = Form(...),  # noqa: B008
    file: UploadFile = File(...),  # noqa: B008
) -> EvidenceResponse:
    """Validate and store one citizen evidence upload for a report."""
    await enforce_rate_limit(
        request,
        operation=RateLimitOperation.UPLOAD,
        target_type="report",
        target_id=report_id,
    )
    return await service.upload_report_evidence_by_id(
        session, report_id, uploader_id, file
    )


@router.post(
    "/projects/{project_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_evidence(
    project_id: UUID,
    session: SessionDep,
    request: Request,
    uploader_id: UUID = Form(...),  # noqa: B008
    comment_id: UUID | None = Form(None),  # noqa: B008
    file: UploadFile = File(...),  # noqa: B008
) -> EvidenceResponse:
    """Validate and store one citizen evidence upload for a project."""
    await enforce_rate_limit(
        request,
        operation=RateLimitOperation.UPLOAD,
        target_type="project",
        target_id=project_id,
    )
    return await service.upload_project_evidence(
        session, project_id, uploader_id, comment_id, file
    )


@router.post(
    "/projects/{project_id}/reports/{report_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report_evidence(
    project_id: UUID,
    report_id: UUID,
    session: SessionDep,
    request: Request,
    uploader_id: UUID = Form(...),  # noqa: B008
    comment_id: UUID | None = Form(None),  # noqa: B008
    file: UploadFile = File(...),  # noqa: B008
) -> EvidenceResponse:
    """Validate and store one citizen evidence upload for an issue report."""
    await enforce_rate_limit(
        request,
        operation=RateLimitOperation.UPLOAD,
        target_type="report",
        target_id=report_id,
    )
    return await service.upload_report_evidence(
        session, project_id, report_id, uploader_id, comment_id, file
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: UUID,
    session: SessionDep,
) -> EvidenceResponse:
    """Return evidence metadata without retrieving uploaded file content."""
    return await service.get_evidence(session, evidence_id)


@router.get("/evidence/{evidence_id}/download")
async def download_evidence(
    evidence_id: UUID,
    session: SessionDep,
) -> Response:
    """Download the original file for explicitly public evidence."""
    download = await service.download_evidence(session, evidence_id)
    return Response(
        content=download.content,
        media_type=download.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{download.filename}"',
        },
    )


@router.get(
    "/evidence/{evidence_id}/processing",
    response_model=EvidenceProcessingResponse,
)
async def get_evidence_processing(
    evidence_id: UUID,
    session: SessionDep,
) -> EvidenceProcessingResponse:
    """Return processing state, safe history, and derived-artifact lineage."""
    return await service.get_processing(session, evidence_id)
