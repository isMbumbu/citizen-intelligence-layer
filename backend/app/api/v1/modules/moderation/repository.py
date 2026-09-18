"""Asynchronous persistence functions for moderation history."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.enums import ModerationTargetType
from app.models.moderation import ModerationHistory


async def create(
    session: AsyncSession,
    history: ModerationHistory,
) -> ModerationHistory:
    """Persist one moderation decision and its resulting content state."""
    session.add(history)
    await session.commit()
    await session.refresh(history)
    logger.info(
        "Stored moderation history id=%s target_type=%s target_id=%s action=%s",
        history.id,
        history.target_type,
        history.target_id,
        history.action,
    )
    return history


async def list_for_target(
    session: AsyncSession,
    target_type: ModerationTargetType,
    target_id: UUID,
) -> list[ModerationHistory]:
    """Return moderation history in deterministic chronological order."""
    result = await session.exec(
        select(ModerationHistory)
        .where(
            ModerationHistory.target_type == target_type,
            ModerationHistory.target_id == target_id,
        )
        .order_by(
            col(ModerationHistory.created_at),
            col(ModerationHistory.id),
        )
    )
    history = list(result.all())
    logger.info(
        "Listed moderation history target_type=%s target_id=%s count=%s",
        target_type,
        target_id,
        len(history),
    )
    return history
