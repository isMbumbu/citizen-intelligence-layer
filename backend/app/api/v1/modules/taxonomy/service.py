"""Application functions for public project-taxonomy reference data."""

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.taxonomy import repository
from app.api.v1.modules.taxonomy.schemas import (
    ProjectCategoryResponse,
    ProjectSubtypeResponse,
)
from app.core.logging import logger
from app.models.vertical_slice import ProjectCategory, ProjectSubtype


async def list_categories(session: AsyncSession) -> list[ProjectCategoryResponse]:
    """Return active categories and their active subtypes for public selection."""
    try:
        categories = await repository.list_active_categories(session)
        subtypes = await repository.list_active_subtypes(
            session,
            {category.id for category in categories},
        )
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to retrieve project taxonomy")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project categories.",
        ) from error
    return _category_responses(categories, subtypes)


async def list_subtypes(
    session: AsyncSession,
    category_id: UUID,
) -> list[ProjectSubtypeResponse]:
    """Return active subtypes for one active category with a stable 404 state."""
    try:
        category = await repository.get_active_category(session, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project category not found.",
            )
        subtypes = await repository.list_active_subtypes(session, {category.id})
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to retrieve project category id=%s", category_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project subtypes.",
        ) from error
    return [_subtype_response(subtype) for subtype in subtypes]


def _category_responses(
    categories: list[ProjectCategory],
    subtypes: list[ProjectSubtype],
) -> list[ProjectCategoryResponse]:
    """Attach category-owned subtypes without exposing persistence models."""
    grouped: defaultdict[UUID, list[ProjectSubtype]] = defaultdict(list)
    for subtype in subtypes:
        grouped[subtype.category_id].append(subtype)
    return [
        ProjectCategoryResponse(
            id=category.id,
            code=category.code,
            name=category.name,
            description=category.description,
            subtypes=[_subtype_response(subtype) for subtype in grouped[category.id]],
        )
        for category in categories
    ]


def _subtype_response(subtype: ProjectSubtype) -> ProjectSubtypeResponse:
    """Convert one reference-data subtype to its public API contract."""
    return ProjectSubtypeResponse(
        id=subtype.id,
        code=subtype.code,
        name=subtype.name,
        description=subtype.description,
    )
