"""Internal services for claim verification review requests."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.verification import repository
from app.models.enums import ClaimReviewRequestType
from app.models.vertical_slice import ClaimReviewRequest


async def create_claim_review_request(
    session: AsyncSession,
    claim_id: UUID,
    request_type: ClaimReviewRequestType,
    content: str,
) -> ClaimReviewRequest:
    """Persist one internal correction or review appeal request."""
    claim = await repository.get_claim(session, claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found.",
        )
    try:
        request_type = ClaimReviewRequestType(request_type)
        request = ClaimReviewRequest(
            claim_id=claim_id,
            request_type=request_type,
            content=content,
        )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The claim review request is invalid.",
        ) from None
    return await repository.create_claim_review_request(
        session,
        request,
    )
