"""Application functions for citizen-submitted project comments."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.comments import repository
from app.api.v1.modules.comments.schemas import (
    CitizenCommentCreateRequest,
    CitizenCommentResponse,
    CommentReportCreateRequest,
    CommentReportResponse,
)
from app.api.v1.modules.projects import repository as projects_repository
from app.core.logging import logger
from app.models.citizen_comments import CitizenComment, CommentReport
from app.models.enums import (
    CommentModerationState,
    CommentReportStatus,
    CommentStatus,
    CommentVisibility,
)


async def create_comment(
    session: AsyncSession,
    project_id: UUID,
    payload: CitizenCommentCreateRequest,
) -> CitizenCommentResponse:
    """Create a citizen comment after validating its project and parent."""
    project = await projects_repository.get(session, project_id)
    if project is None:
        logger.info("Rejected comment for unknown project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    if payload.parent_comment_id is not None:
        parent = await repository.get_comment(session, payload.parent_comment_id)
        if parent is None or parent.project_id != project_id:
            logger.info(
                "Rejected comment with invalid parent id=%s project_id=%s",
                payload.parent_comment_id,
                project_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found for project.",
            )
    try:
        comment = await repository.create_comment(
            session,
            CitizenComment(
                project_id=project_id,
                parent_comment_id=payload.parent_comment_id,
                author_id=payload.author_id,
                content=payload.content,
            ),
        )
    except Exception as error:
        await session.rollback()
        logger.exception(
            "Unable to create citizen comment for project id=%s", project_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create comment.",
        ) from error
    logger.info("Created citizen comment id=%s project_id=%s", comment.id, project_id)
    return _comment_response(comment)


async def list_comments(
    session: AsyncSession,
    project_id: UUID,
) -> list[CitizenCommentResponse]:
    """List publicly visible citizen comments for an existing project."""
    project = await projects_repository.get(session, project_id)
    if project is None:
        logger.info("Rejected comment listing for unknown project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    comments = await repository.list_comments(session, project_id)
    comments = [
        comment
        for comment in comments
        if comment.moderation_state
        not in {
            CommentModerationState.HIDDEN.value,
            CommentModerationState.REMOVED.value,
        }
    ]
    logger.info(
        "Listed %s citizen comment(s) for project id=%s", len(comments), project_id
    )
    return [_comment_response(comment) for comment in comments]


async def report_comment(
    session: AsyncSession,
    comment_id: UUID,
    payload: CommentReportCreateRequest,
) -> CommentReportResponse:
    """Submit a citizen abuse or policy report for an existing comment."""
    comment = await repository.get_comment(session, comment_id)
    if comment is None:
        logger.info("Rejected report for unknown comment id=%s", comment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )
    try:
        report = await repository.create_report(
            session,
            CommentReport(
                comment_id=comment_id,
                reporter_id=payload.reporter_id,
                reason=payload.reason.value,
            ),
        )
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to report citizen comment id=%s", comment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to report comment.",
        ) from error
    logger.info("Reported citizen comment id=%s", comment_id)
    return CommentReportResponse(
        id=report.id,
        comment_id=report.comment_id,
        reporter_id=report.reporter_id,
        reason=payload.reason,
        status=CommentReportStatus(report.status),
        submitted_at=report.submitted_at,
    )


def _comment_response(comment: CitizenComment) -> CitizenCommentResponse:
    return CitizenCommentResponse(
        id=comment.id,
        project_id=comment.project_id,
        parent_comment_id=comment.parent_comment_id,
        author_id=comment.author_id,
        content=comment.content,
        status=CommentStatus(comment.status),
        moderation_state=CommentModerationState(comment.moderation_state),
        visibility=CommentVisibility(comment.visibility),
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )
