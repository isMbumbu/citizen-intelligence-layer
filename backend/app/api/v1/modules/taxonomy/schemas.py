"""Pydantic contracts for project taxonomy reference data."""

from uuid import UUID

from pydantic import BaseModel, Field


class ProjectSubtypeResponse(BaseModel):
    """A public, active subtype belonging to one project category."""

    id: UUID
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)


class ProjectCategoryResponse(BaseModel):
    """An active category with its active subtype reference data."""

    id: UUID
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    subtypes: list[ProjectSubtypeResponse]
