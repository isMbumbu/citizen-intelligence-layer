"""Thin HTTP routes for citizen-submitted project comments."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.comments import service
from app.api.v1.modules.comments.schemas import (
    CitizenCommentCreateRequest,
    CitizenCommentResponse,
    CommentReportCreateRequest,
    CommentReportResponse,
)
from app.core.database import get_session

router = APIRouter(tags=["citizen comments"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/projects/{project_id}/comments",
    response_model=CitizenCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_comment(
    project_id: UUID,
    payload: CitizenCommentCreateRequest,
    session: SessionDep,
) -> CitizenCommentResponse:
    """Create one citizen-submitted comment on a project."""
    return await service.create_comment(session, project_id, payload)


@router.get(
    "/projects/{project_id}/comments",
    response_model=list[CitizenCommentResponse],
)
async def list_project_comments(
    project_id: UUID,
    session: SessionDep,
) -> list[CitizenCommentResponse]:
    """List publicly visible citizen-submitted comments for a project."""
    return await service.list_comments(session, project_id)


@router.post(
    "/comments/{comment_id}/reports",
    response_model=CommentReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def report_project_comment(
    comment_id: UUID,
    payload: CommentReportCreateRequest,
    session: SessionDep,
) -> CommentReportResponse:
    """Report one citizen comment for later abuse or policy review."""
    return await service.report_comment(session, comment_id, payload)
