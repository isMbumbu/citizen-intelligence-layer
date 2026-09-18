"""Application functions for protected comment and evidence moderation."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.comments import repository as comments_repository
from app.api.v1.modules.evidence import repository as evidence_repository
from app.api.v1.modules.moderation import repository
from app.api.v1.modules.moderation.schemas import (
    ModerationHistoryResponse,
    ModerationRequest,
)
from app.core.logging import logger
from app.core.security import CurrentModerator
from app.models.citizen_comments import CitizenComment
from app.models.enums import (
    ModerationAction,
    ModerationTargetType,
)
from app.models.evidence import EvidenceRecord
from app.models.moderation import ModerationHistory

_Target = CitizenComment | EvidenceRecord


async def moderate_comment(
    session: AsyncSession,
    comment_id: UUID,
    payload: ModerationRequest,
    actor: CurrentModerator,
) -> ModerationHistoryResponse:
    """Apply one authorized moderation action to a citizen comment."""
    comment = await comments_repository.get_comment(session, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found."
        )
    history = await _moderate(
        session,
        target=comment,
        target_type=ModerationTargetType.COMMENT,
        target_id=comment_id,
        payload=payload,
        actor=actor,
    )
    return _response(history)


async def moderate_evidence(
    session: AsyncSession,
    evidence_id: UUID,
    payload: ModerationRequest,
    actor: CurrentModerator,
) -> ModerationHistoryResponse:
    """Apply one authorized moderation action to citizen evidence."""
    evidence = await evidence_repository.get(session, evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found."
        )
    history = await _moderate(
        session,
        target=evidence,
        target_type=ModerationTargetType.EVIDENCE,
        target_id=evidence_id,
        payload=payload,
        actor=actor,
    )
    return _response(history)


async def comment_history(
    session: AsyncSession,
    comment_id: UUID,
) -> list[ModerationHistoryResponse]:
    """Return moderation history for an existing comment."""
    if await comments_repository.get_comment(session, comment_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found."
        )
    return [
        _response(item)
        for item in await repository.list_for_target(
            session,
            ModerationTargetType.COMMENT,
            comment_id,
        )
    ]


async def evidence_history(
    session: AsyncSession,
    evidence_id: UUID,
) -> list[ModerationHistoryResponse]:
    """Return moderation history for existing citizen evidence."""
    if await evidence_repository.get(session, evidence_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found."
        )
    return [
        _response(item)
        for item in await repository.list_for_target(
            session,
            ModerationTargetType.EVIDENCE,
            evidence_id,
        )
    ]


async def _moderate(
    session: AsyncSession,
    *,
    target: _Target,
    target_type: ModerationTargetType,
    target_id: UUID,
    payload: ModerationRequest,
    actor: CurrentModerator,
) -> ModerationHistory:
    """Apply a validated transition and persist its moderation history."""
    current_state = _state(target)
    resulting_state = _next_state(current_state, payload.action)
    if resulting_state is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid moderation transition: {current_state} -> {payload.action}."
            ),
        )
    if resulting_state == current_state:
        existing = await _latest_matching_history(
            session,
            target_type=target_type,
            target_id=target_id,
            action=payload.action,
            reason=payload.reason,
            resulting_state=resulting_state,
        )
        if existing is not None:
            logger.info(
                "Repeated moderation action was idempotent target_type=%s "
                "target_id=%s action=%s",
                target_type,
                target_id,
                payload.action,
            )
            return existing

    history = ModerationHistory(
        target_type=target_type,
        target_id=target_id,
        actor_id=actor.actor_id,
        action=payload.action,
        reason=payload.reason,
        previous_state=current_state,
        resulting_state=resulting_state,
        notes=payload.notes,
    )
    _set_state(target, resulting_state)
    try:
        result = await repository.create(session, history)
    except Exception:
        await session.rollback()
        raise
    logger.info(
        "Applied moderation action target_type=%s target_id=%s action=%s "
        "previous_state=%s resulting_state=%s",
        target_type,
        target_id,
        payload.action,
        current_state,
        resulting_state,
    )
    return result


async def _latest_matching_history(
    session: AsyncSession,
    *,
    target_type: ModerationTargetType,
    target_id: UUID,
    action: ModerationAction,
    reason: object,
    resulting_state: str,
) -> ModerationHistory | None:
    """Return the latest identical action when it is safely idempotent."""
    history = await repository.list_for_target(session, target_type, target_id)
    if history:
        item = history[-1]
        if (
            item.action == action
            and item.reason == reason
            and item.resulting_state == resulting_state
        ):
            return item
    return None


def _state(target: _Target) -> str:
    """Read the shared moderation-state field from a target record."""
    return target.moderation_state


def _set_state(target: _Target, state: str) -> None:
    """Apply a moderation state without changing unrelated lifecycle fields."""
    target.moderation_state = state


def _next_state(current: str, action: ModerationAction) -> str | None:
    """Resolve the contract transition matrix for one moderation action."""
    transitions = {
        "PENDING": {
            ModerationAction.FLAG: "FLAGGED",
            ModerationAction.HIDE: "HIDDEN",
            ModerationAction.REMOVE: "REMOVED",
        },
        "FLAGGED": {
            ModerationAction.FLAG: "FLAGGED",
            ModerationAction.HIDE: "HIDDEN",
            ModerationAction.REMOVE: "REMOVED",
            ModerationAction.RESTORE: "PENDING",
        },
        "HIDDEN": {
            ModerationAction.FLAG: "FLAGGED",
            ModerationAction.HIDE: "HIDDEN",
            ModerationAction.REMOVE: "REMOVED",
            ModerationAction.RESTORE: "PENDING",
        },
        "REMOVED": {
            ModerationAction.REMOVE: "REMOVED",
            ModerationAction.RESTORE: "PENDING",
        },
    }
    return transitions.get(current, {}).get(action)


def _response(history: ModerationHistory) -> ModerationHistoryResponse:
    """Convert internal moderation history to its protected API response."""
    return ModerationHistoryResponse.model_validate(history, from_attributes=True)
