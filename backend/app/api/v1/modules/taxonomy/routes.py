"""Thin HTTP routes for project taxonomy reference-data lookup."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.taxonomy import service
from app.api.v1.modules.taxonomy.schemas import (
    ProjectCategoryResponse,
    ProjectSubtypeResponse,
)
from app.core.database import get_session

router = APIRouter(prefix="/project-categories", tags=["project taxonomy"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[ProjectCategoryResponse])
async def list_project_categories(
    session: SessionDep,
) -> list[ProjectCategoryResponse]:
    """List active project categories with their active subtype hierarchy."""
    return await service.list_categories(session)


@router.get(
    "/{category_id}/subtypes",
    response_model=list[ProjectSubtypeResponse],
)
async def list_project_subtypes(
    category_id: UUID,
    session: SessionDep,
) -> list[ProjectSubtypeResponse]:
    """List active project subtypes for one active category."""
    return await service.list_subtypes(session, category_id)
