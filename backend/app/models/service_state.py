"""Minimal persistence model used to verify the platform migration path."""

from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ServiceState(SQLModel, table=True):
    """A non-business record proving SQLModel/Alembic/PostgreSQL integration."""

    __tablename__: ClassVar[str] = "service_states"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(index=True, max_length=64)
    value: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
