"""Persistence model for append-only citizen-content moderation history."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel

from app.models.enums import (
    ModerationAction,
    ModerationReason,
    ModerationTargetType,
)
from app.models.vertical_slice import utc_now


class ModerationHistory(SQLModel, table=True):
    """One moderation decision for a comment or citizen evidence record."""

    __tablename__: ClassVar[str] = "moderation_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    target_type: ModerationTargetType = Field(index=True)
    target_id: UUID = Field(index=True)
    actor_id: UUID = Field(index=True)
    action: ModerationAction
    reason: ModerationReason
    previous_state: str = Field(max_length=30)
    resulting_state: str = Field(max_length=30)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
