"""Focused behavior tests for CIV-001 citizen comments."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.comments.repository as comments_repository
import app.api.v1.modules.comments.service as comments_service
from app.api.v1.modules.comments.schemas import (
    CitizenCommentCreateRequest,
    CommentReportCreateRequest,
)
from app.api.v1.modules.projects import repository as projects_repository
from app.models.citizen_comments import CitizenComment, CommentReport
from app.models.enums import CommentReportReason
from app.models.vertical_slice import Project

PROJECT_ID = uuid4()
AUTHOR_ID = uuid4()
COMMENT_ID = uuid4()


def _project() -> Project:
    return Project(
        id=PROJECT_ID,
        demo_key="comment-project",
        name="Comment project",
        description="A project used by CIV-001 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=datetime(2026, 1, 1).date(),
        planned_completion_date=datetime(2026, 12, 31).date(),
    )


def _comment(*, project_id: object = PROJECT_ID) -> CitizenComment:
    now = datetime.now(UTC)
    return CitizenComment(
        id=COMMENT_ID,
        project_id=project_id,
        author_id=AUTHOR_ID,
        content="A citizen-submitted observation.",
        created_at=now,
        updated_at=now,
    )


async def test_create_comment_attaches_project_author_and_citizen_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    created = _comment()
    monkeypatch.setattr(
        comments_repository,
        "create_comment",
        AsyncMock(return_value=created),
    )

    response = await comments_service.create_comment(
        AsyncMock(),
        PROJECT_ID,
        CitizenCommentCreateRequest(
            author_id=AUTHOR_ID,
            content="  A citizen-submitted observation.  ",
        ),
    )

    assert response.project_id == PROJECT_ID
    assert response.author_id == AUTHOR_ID
    assert response.is_citizen_submitted is True
    assert response.trust_label == "CITIZEN_SUBMITTED_INFORMATION"
    assert response.moderation_state.value == "PENDING"
    assert response.visibility.value == "PUBLIC"
    stored = comments_repository.create_comment.await_args.args[1]
    assert stored.content == "A citizen-submitted observation."


async def test_create_comment_rejects_unknown_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await comments_service.create_comment(
            AsyncMock(),
            PROJECT_ID,
            CitizenCommentCreateRequest(
                author_id=AUTHOR_ID,
                content="A comment for a missing project.",
            ),
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found."


async def test_create_comment_supports_parent_threading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = _comment()
    created = _comment()
    created.parent_comment_id = COMMENT_ID
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        comments_repository, "get_comment", AsyncMock(return_value=parent)
    )
    monkeypatch.setattr(
        comments_repository,
        "create_comment",
        AsyncMock(return_value=created),
    )

    response = await comments_service.create_comment(
        AsyncMock(),
        PROJECT_ID,
        CitizenCommentCreateRequest(
            author_id=AUTHOR_ID,
            content="A reply to the original citizen comment.",
            parent_comment_id=COMMENT_ID,
        ),
    )

    assert response.parent_comment_id == COMMENT_ID


async def test_comment_listing_is_publicly_labeled_and_excludes_private_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        comments_repository,
        "list_comments",
        AsyncMock(return_value=[_comment()]),
    )

    response = await comments_service.list_comments(AsyncMock(), PROJECT_ID)

    assert len(response) == 1
    assert response[0].trust_label == "CITIZEN_SUBMITTED_INFORMATION"
    assert response[0].is_citizen_submitted is True
    comments_repository.list_comments.assert_awaited_once_with(
        comments_repository.list_comments.await_args.args[0], PROJECT_ID
    )


async def test_report_comment_persists_reason_and_submitted_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        comments_repository, "get_comment", AsyncMock(return_value=_comment())
    )
    report = CommentReport(
        id=uuid4(),
        comment_id=COMMENT_ID,
        reporter_id=AUTHOR_ID,
        reason=CommentReportReason.HARASSMENT.value,
    )
    monkeypatch.setattr(
        comments_repository,
        "create_report",
        AsyncMock(return_value=report),
    )

    response = await comments_service.report_comment(
        AsyncMock(),
        COMMENT_ID,
        CommentReportCreateRequest(
            reporter_id=AUTHOR_ID,
            reason=CommentReportReason.HARASSMENT,
        ),
    )

    assert response.comment_id == COMMENT_ID
    assert response.reason == CommentReportReason.HARASSMENT
    assert response.status.value == "SUBMITTED"
    stored = comments_repository.create_report.await_args.args[1]
    assert stored.reason == "HARASSMENT"


async def test_report_comment_rejects_unknown_comment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        comments_repository, "get_comment", AsyncMock(return_value=None)
    )

    with pytest.raises(HTTPException) as error:
        await comments_service.report_comment(
            AsyncMock(),
            COMMENT_ID,
            CommentReportCreateRequest(
                reporter_id=AUTHOR_ID,
                reason=CommentReportReason.SPAM,
            ),
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Comment not found."
