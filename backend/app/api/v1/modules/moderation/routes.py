"""Protected moderation routes for citizen comments and evidence."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.moderation import service
from app.api.v1.modules.moderation.schemas import (
    ModerationHistoryResponse,
    ModerationRequest,
)
from app.core.database import get_session
from app.core.security import CurrentModerator, get_authorized_moderator

router = APIRouter(tags=["moderation"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
ModeratorDep = Annotated[CurrentModerator, Depends(get_authorized_moderator)]


@router.post(
    "/comments/{comment_id}/moderation",
    response_model=ModerationHistoryResponse,
    status_code=201,
)
async def moderate_comment(
    comment_id: UUID,
    payload: ModerationRequest,
    session: SessionDep,
    actor: ModeratorDep,
) -> ModerationHistoryResponse:
    """Apply one protected moderation action to a citizen comment."""
    return await service.moderate_comment(session, comment_id, payload, actor)


@router.post(
    "/evidence/{evidence_id}/moderation",
    response_model=ModerationHistoryResponse,
    status_code=201,
)
async def moderate_evidence(
    evidence_id: UUID,
    payload: ModerationRequest,
    session: SessionDep,
    actor: ModeratorDep,
) -> ModerationHistoryResponse:
    """Apply one protected moderation action to citizen evidence."""
    return await service.moderate_evidence(session, evidence_id, payload, actor)


@router.get(
    "/comments/{comment_id}/moderation-history",
    response_model=list[ModerationHistoryResponse],
)
async def comment_moderation_history(
    comment_id: UUID,
    session: SessionDep,
    _: ModeratorDep,
) -> list[ModerationHistoryResponse]:
    """Return protected moderation history for a citizen comment."""
    return await service.comment_history(session, comment_id)


@router.get(
    "/evidence/{evidence_id}/moderation-history",
    response_model=list[ModerationHistoryResponse],
)
async def evidence_moderation_history(
    evidence_id: UUID,
    session: SessionDep,
    _: ModeratorDep,
) -> list[ModerationHistoryResponse]:
    """Return protected moderation history for citizen evidence."""
    return await service.evidence_history(session, evidence_id)
