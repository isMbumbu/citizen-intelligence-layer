"""Asynchronous SQLModel queries for project verification records."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.vertical_slice import Claim, ClaimReviewRequest, ProjectVerification


async def get_latest_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> ProjectVerification | None:
    """Return the latest explicitly recorded verification state."""
    result = await session.exec(
        select(ProjectVerification)
        .where(ProjectVerification.project_id == project_id)
        .order_by(col(ProjectVerification.recorded_at).desc())
        .limit(1)
    )
    return result.first()


async def get_claim(
    session: AsyncSession,
    claim_id: UUID,
) -> Claim | None:
    """Return one material claim by identifier."""
    return await session.get(Claim, claim_id)


async def create_claim_review_request(
    session: AsyncSession,
    request: ClaimReviewRequest,
) -> ClaimReviewRequest:
    """Persist one append-only claim review request."""
    try:
        session.add(request)
        await session.commit()
        await session.refresh(request)
    except Exception:
        await session.rollback()
        logger.exception("Unable to store claim review request")
        raise
    return request


async def list_claim_review_requests(
    session: AsyncSession,
    claim_id: UUID,
) -> list[ClaimReviewRequest]:
    """Return claim review requests in deterministic chronological order."""
    result = await session.exec(
        select(ClaimReviewRequest)
        .where(ClaimReviewRequest.claim_id == claim_id)
        .order_by(
            col(ClaimReviewRequest.created_at),
            col(ClaimReviewRequest.id),
        )
    )
    return list(result.all())
