"""Thin HTTP routes for evidence metadata."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
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
    PublicEvidencePage,
)
from app.core.database import get_session
from app.core.rate_limit import RateLimitOperation, enforce_rate_limit
from app.core.security import CurrentModerator, get_optional_current_actor

router = APIRouter(tags=["evidence"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
OptionalActorDep = Annotated[
    CurrentModerator | None, Depends(get_optional_current_actor)
]


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


@router.get("/projects/{project_id}/evidence", response_model=list[EvidenceResponse])
async def list_project_evidence(
    project_id: UUID,
    session: SessionDep,
) -> list[EvidenceResponse]:
    """List public citizen evidence for a project, including report and comment
    attachments, newest first."""
    return await service.list_public_evidence(session, project_id=project_id)


@router.get("/reports/{report_id}/evidence", response_model=list[EvidenceResponse])
async def list_report_evidence(
    report_id: UUID,
    session: SessionDep,
) -> list[EvidenceResponse]:
    """List public citizen evidence attached to a report, newest first."""
    return await service.list_public_evidence(session, report_id=report_id)


@router.get("/comments/{comment_id}/evidence", response_model=list[EvidenceResponse])
async def list_comment_evidence(
    comment_id: UUID,
    session: SessionDep,
) -> list[EvidenceResponse]:
    """List public citizen evidence attached to a comment, newest first."""
    return await service.list_public_evidence(session, comment_id=comment_id)


@router.get("/evidence", response_model=PublicEvidencePage)
async def browse_evidence(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 24,
    project_id: UUID | None = None,
    category_id: UUID | None = None,
    county: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    kind: Literal["image", "document"] | None = None,
) -> PublicEvidencePage:
    """Browse public citizen evidence with project context, newest first.

    Cards never include uploader identifiers, checksums, filenames, or storage
    details.
    """
    return await service.browse_public_evidence(
        session,
        project_id=project_id,
        category_id=category_id,
        county=county.strip() if county is not None else None,
        kind=kind,
        page=page,
        page_size=page_size,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: UUID,
    session: SessionDep,
    actor: OptionalActorDep = None,
) -> EvidenceResponse:
    """Return evidence metadata without retrieving uploaded file content."""
    return await service.get_evidence(session, evidence_id, actor=actor)


@router.get("/evidence/{evidence_id}/download")
async def download_evidence(
    evidence_id: UUID,
    session: SessionDep,
    actor: OptionalActorDep = None,
) -> Response:
    """Download the original file for explicitly public evidence."""
    download = await service.download_evidence(
        session,
        evidence_id,
        actor=actor,
    )
    # Images (re-encoded without metadata at upload) display in the browser;
    # PDFs and anything else still download.
    disposition = "inline" if download.mime_type.startswith("image/") else "attachment"
    return Response(
        content=download.content,
        media_type=download.mime_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{download.filename}"',
            "Cache-Control": "public, max-age=300",
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
