"""Focused behavior tests for MOD-001 moderation."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.comments.repository as comments_repository
import app.api.v1.modules.comments.service as comments_service
import app.api.v1.modules.evidence.repository as evidence_repository
import app.api.v1.modules.evidence.service as evidence_service
import app.api.v1.modules.moderation.repository as moderation_repository
import app.api.v1.modules.moderation.service as moderation_service
from app.api.v1.modules.comments.schemas import CommentReportCreateRequest
from app.api.v1.modules.moderation.schemas import ModerationRequest
from app.core.security import (
    MODERATE_CONTENT_PERMISSION,
    CurrentModerator,
    get_current_moderator,
    require_moderation_permission,
)
from app.models.citizen_comments import CitizenComment, CommentReport
from app.models.enums import (
    CommentReportReason,
    CommentReportStatus,
    ModerationAction,
    ModerationReason,
    ModerationTargetType,
)
from app.models.evidence import EvidenceRecord
from app.models.moderation import ModerationHistory

COMMENT_ID = uuid4()
EVIDENCE_ID = uuid4()
ACTOR_ID = uuid4()


def _comment(state: str = "PENDING") -> CitizenComment:
    now = datetime.now(UTC)
    return CitizenComment(
        id=COMMENT_ID,
        project_id=uuid4(),
        author_id=uuid4(),
        content="Original citizen content remains stored.",
        moderation_state=state,
        created_at=now,
        updated_at=now,
    )


def _evidence(state: str = "PENDING") -> EvidenceRecord:
    return EvidenceRecord(
        id=EVIDENCE_ID,
        project_id=uuid4(),
        uploader_id=uuid4(),
        original_filename="evidence.png",
        mime_type="image/png",
        file_size_bytes=10,
        checksum_sha256="a" * 64,
        storage_key="evidence/object.png",
        moderation_state=state,
        visibility="PUBLIC",
    )


def _actor() -> CurrentModerator:
    return CurrentModerator(
        actor_id=ACTOR_ID,
        permissions=frozenset({MODERATE_CONTENT_PERMISSION}),
    )


def _request(
    action: ModerationAction,
    *,
    notes: str | None = "Private decision context.",
) -> ModerationRequest:
    return ModerationRequest(
        action=action,
        reason=ModerationReason.HARASSMENT,
        notes=notes,
    )


async def _comment_moderation(
    monkeypatch: pytest.MonkeyPatch,
    comment: CitizenComment,
    requests: list[ModerationRequest],
) -> tuple[list[ModerationHistory], list[object]]:
    histories: list[ModerationHistory] = []
    monkeypatch.setattr(
        comments_repository,
        "get_comment",
        AsyncMock(return_value=comment),
    )

    async def store(session: object, history: ModerationHistory) -> ModerationHistory:
        histories.append(history)
        return history

    monkeypatch.setattr(moderation_repository, "create", AsyncMock(side_effect=store))
    monkeypatch.setattr(
        moderation_repository,
        "list_for_target",
        AsyncMock(return_value=histories),
    )
    responses = [
        await moderation_service.moderate_comment(
            AsyncMock(), COMMENT_ID, request, _actor()
        )
        for request in requests
    ]
    return histories, responses


@pytest.mark.parametrize(
    ("action", "expected_state"),
    [
        (ModerationAction.FLAG, "FLAGGED"),
        (ModerationAction.HIDE, "HIDDEN"),
        (ModerationAction.REMOVE, "REMOVED"),
    ],
)
async def test_comment_moderation_persists_action_and_content(
    monkeypatch: pytest.MonkeyPatch,
    action: ModerationAction,
    expected_state: str,
) -> None:
    comment = _comment()
    histories, responses = await _comment_moderation(
        monkeypatch,
        comment,
        [_request(action)],
    )

    assert comment.moderation_state == expected_state
    assert comment.content == "Original citizen content remains stored."
    assert len(histories) == 1
    history = histories[0]
    assert history.actor_id == ACTOR_ID
    assert history.action == action
    assert history.reason == ModerationReason.HARASSMENT
    assert history.previous_state == "PENDING"
    assert history.resulting_state == expected_state
    assert history.notes == "Private decision context."
    assert responses[0].actor_id == ACTOR_ID
    public_response = comments_service._comment_response(comment)
    assert "notes" not in public_response.model_dump()


@pytest.mark.parametrize("state", ["FLAGGED", "HIDDEN", "REMOVED"])
async def test_comment_restore_reopens_moderated_content(
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    comment = _comment(state)
    histories, _ = await _comment_moderation(
        monkeypatch,
        comment,
        [_request(ModerationAction.RESTORE)],
    )

    assert comment.moderation_state == "PENDING"
    assert histories[0].previous_state == state
    assert histories[0].resulting_state == "PENDING"


async def test_repeated_identical_comment_action_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    comment = _comment()
    histories, responses = await _comment_moderation(
        monkeypatch,
        comment,
        [_request(ModerationAction.FLAG), _request(ModerationAction.FLAG)],
    )

    assert len(histories) == 1
    assert responses[0].id == responses[1].id


async def test_invalid_comment_transition_returns_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    comment = _comment("PENDING")
    monkeypatch.setattr(
        comments_repository, "get_comment", AsyncMock(return_value=comment)
    )
    monkeypatch.setattr(
        moderation_repository, "list_for_target", AsyncMock(return_value=[])
    )

    with pytest.raises(HTTPException) as error:
        await moderation_service.moderate_comment(
            AsyncMock(), COMMENT_ID, _request(ModerationAction.RESTORE), _actor()
        )

    assert error.value.status_code == 409


async def test_evidence_moderation_and_history_are_separate_from_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence()
    histories: list[ModerationHistory] = []
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    async def store(session: object, history: ModerationHistory) -> ModerationHistory:
        histories.append(history)
        return history

    monkeypatch.setattr(moderation_repository, "create", AsyncMock(side_effect=store))
    monkeypatch.setattr(
        moderation_repository,
        "list_for_target",
        AsyncMock(return_value=histories),
    )

    result = await moderation_service.moderate_evidence(
        AsyncMock(), EVIDENCE_ID, _request(ModerationAction.HIDE), _actor()
    )

    assert evidence.moderation_state == "HIDDEN"
    assert evidence.processing_state == "RAW"
    assert result.target_type == ModerationTargetType.EVIDENCE
    assert result.notes == "Private decision context."


@pytest.mark.parametrize(
    ("action", "expected_state"),
    [
        (ModerationAction.FLAG, "FLAGGED"),
        (ModerationAction.HIDE, "HIDDEN"),
        (ModerationAction.REMOVE, "REMOVED"),
    ],
)
async def test_evidence_moderation_actions_persist_state(
    monkeypatch: pytest.MonkeyPatch,
    action: ModerationAction,
    expected_state: str,
) -> None:
    evidence = _evidence()
    histories: list[ModerationHistory] = []

    async def store(session: object, history: ModerationHistory) -> ModerationHistory:
        histories.append(history)
        return history

    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))
    monkeypatch.setattr(moderation_repository, "create", AsyncMock(side_effect=store))
    monkeypatch.setattr(
        moderation_repository,
        "list_for_target",
        AsyncMock(return_value=histories),
    )

    await moderation_service.moderate_evidence(
        AsyncMock(), EVIDENCE_ID, _request(action), _actor()
    )

    assert evidence.moderation_state == expected_state
    assert evidence.processing_state == "RAW"
    assert histories[0].previous_state == "PENDING"
    assert histories[0].resulting_state == expected_state


@pytest.mark.parametrize("state", ["FLAGGED", "HIDDEN", "REMOVED"])
async def test_evidence_restore_returns_to_pending(
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    evidence = _evidence(state)
    histories: list[ModerationHistory] = []

    async def store(session: object, history: ModerationHistory) -> ModerationHistory:
        histories.append(history)
        return history

    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))
    monkeypatch.setattr(moderation_repository, "create", AsyncMock(side_effect=store))
    monkeypatch.setattr(
        moderation_repository,
        "list_for_target",
        AsyncMock(return_value=histories),
    )

    await moderation_service.moderate_evidence(
        AsyncMock(), EVIDENCE_ID, _request(ModerationAction.RESTORE), _actor()
    )

    assert evidence.moderation_state == "PENDING"
    assert histories[0].previous_state == state


@pytest.mark.parametrize("state", ["HIDDEN", "REMOVED"])
async def test_hidden_or_removed_evidence_metadata_is_not_public(
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    evidence = _evidence(state)
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    with pytest.raises(HTTPException) as error:
        await evidence_service.get_evidence(AsyncMock(), EVIDENCE_ID)

    assert error.value.status_code == 404


async def test_public_comment_listing_excludes_hidden_and_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _comment()
    hidden = _comment("HIDDEN")
    removed = _comment("REMOVED")
    monkeypatch.setattr(
        comments_repository,
        "get_comment",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(
        comments_repository,
        "list_comments",
        AsyncMock(return_value=[project, hidden, removed]),
    )

    result = await comments_service.list_comments(AsyncMock(), project.project_id)

    assert len(result) == 1
    assert result[0].moderation_state.value == "PENDING"


async def test_comment_report_does_not_create_moderation_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    comment = _comment()
    monkeypatch.setattr(
        comments_repository, "get_comment", AsyncMock(return_value=comment)
    )
    report = CommentReport(
        id=uuid4(),
        comment_id=COMMENT_ID,
        reporter_id=uuid4(),
        reason=CommentReportReason.SPAM.value,
        status=CommentReportStatus.SUBMITTED.value,
    )
    create_report = AsyncMock(return_value=report)
    monkeypatch.setattr(comments_repository, "create_report", create_report)
    history = AsyncMock()
    monkeypatch.setattr(moderation_repository, "create", history)
    await comments_service.report_comment(
        AsyncMock(),
        COMMENT_ID,
        CommentReportCreateRequest(
            reporter_id=uuid4(), reason=CommentReportReason.SPAM
        ),
    )
    history.assert_not_awaited()
    assert comment.moderation_state == "PENDING"


async def test_moderator_auth_boundary_fails_closed() -> None:
    with pytest.raises(HTTPException) as error:
        await get_current_moderator()
    assert error.value.status_code == 401

    with pytest.raises(HTTPException) as error:
        require_moderation_permission(CurrentModerator(uuid4(), frozenset()))
    assert error.value.status_code == 403
