"""Asynchronous persistence functions for citizen comments and reports."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.citizen_comments import CitizenComment, CommentReport


async def create_comment(
    session: AsyncSession,
    comment: CitizenComment,
) -> CitizenComment:
    """Persist one citizen comment and refresh its generated fields."""
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    logger.info(
        "Stored citizen comment id=%s project_id=%s", comment.id, comment.project_id
    )
    return comment


async def list_comments(
    session: AsyncSession,
    project_id: UUID,
) -> list[CitizenComment]:
    """Return publicly visible comments for one project in thread order."""
    result = await session.exec(
        select(CitizenComment)
        .where(
            CitizenComment.project_id == project_id,
            col(CitizenComment.visibility) == "PUBLIC",
        )
        .order_by(col(CitizenComment.created_at))
    )
    return list(result.all())


async def get_comment(
    session: AsyncSession,
    comment_id: UUID,
) -> CitizenComment | None:
    """Return one comment by identifier for parent and report validation."""
    return await session.get(CitizenComment, comment_id)


async def create_report(
    session: AsyncSession,
    report: CommentReport,
) -> CommentReport:
    """Persist one citizen report against a comment."""
    session.add(report)
    await session.commit()
    await session.refresh(report)
    logger.info(
        "Stored comment report id=%s comment_id=%s", report.id, report.comment_id
    )
    return report
