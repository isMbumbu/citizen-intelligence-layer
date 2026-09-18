"""Focused behavior tests for RAT-001 rate limiting."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from redis.exceptions import RedisError

import app.api.v1.modules.comments.routes as comments_routes
import app.api.v1.modules.evidence.routes as evidence_routes
import app.core.rate_limit as rate_limit
from app.api.v1.modules.comments.schemas import (
    CitizenCommentCreateRequest,
    CommentReportCreateRequest,
)
from app.core.config import Settings
from app.core.rate_limit import RateLimitOperation

PROJECT_ID = uuid4()
COMMENT_ID = uuid4()
REPORT_ID = uuid4()


class FakeRedis:
    """Minimal Redis double that records atomic fixed-window calls."""

    def __init__(self, result: list[int] | None = None) -> None:
        self.result = result or [1, 600]
        self.calls: list[tuple[str, int, tuple[object, ...]]] = []

    async def eval(
        self,
        script: str,
        number_of_keys: int,
        *keys_and_arguments: object,
    ) -> list[int]:
        self.calls.append((script, number_of_keys, keys_and_arguments))
        return self.result


class FailingRedis:
    async def eval(self, script: str, number_of_keys: int, *values: object) -> None:
        raise RedisError("redis unavailable")


class ClockedRedis:
    """Small fixed-window Redis double with controllable expiry behavior."""

    def __init__(self, clock: list[float]) -> None:
        self.clock = clock
        self.entries: dict[str, tuple[int, float]] = {}

    async def eval(
        self,
        script: str,
        number_of_keys: int,
        key: str,
        window_seconds: int,
    ) -> list[int]:
        entry = self.entries.get(key)
        if entry is None or entry[1] <= self.clock[0]:
            count = 0
            expires_at = self.clock[0] + window_seconds
        else:
            count, expires_at = entry
        count += 1
        self.entries[key] = count, expires_at
        return [count, max(int(expires_at - self.clock[0]), 0)]


def _request(origin: str = "203.0.113.10") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/test",
            "headers": [],
            "client": (origin, 1234),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


@pytest.fixture
def rate_limit_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        rate_limit.settings, "rate_limit_identity_secret", "test-secret"
    )
    monkeypatch.setattr(rate_limit.settings, "rate_limit_key_prefix", "test:ratelimit")
    monkeypatch.setattr(rate_limit.settings, "rate_limit_comment_limit", 2)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_comment_window_seconds", 600)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_report_limit", 2)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_report_window_seconds", 600)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_upload_limit", 2)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_upload_window_seconds", 600)


@pytest.mark.parametrize(
    "field_name",
    [
        "rate_limit_comment_limit",
        "rate_limit_comment_window_seconds",
        "rate_limit_report_limit",
        "rate_limit_report_window_seconds",
        "rate_limit_upload_limit",
        "rate_limit_upload_window_seconds",
    ],
)
@pytest.mark.parametrize("invalid_value", [0, -1])
def test_rate_limit_settings_require_positive_values(
    field_name: str,
    invalid_value: int,
) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        Settings(**{field_name: invalid_value})


async def test_under_limit_and_exact_boundary_are_allowed(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
) -> None:
    redis = FakeRedis([2, 417])
    monkeypatch.setattr(rate_limit, "redis_client", redis)

    await rate_limit.enforce_rate_limit(
        _request(),
        operation=RateLimitOperation.COMMENT,
        target_type="project",
        target_id=PROJECT_ID,
    )

    assert len(redis.calls) == 1
    script, number_of_keys, values = redis.calls[0]
    assert number_of_keys == 1
    assert "INCR" in script
    assert "EXPIRE" in script
    assert values[0] != "203.0.113.10"
    assert values[1] == 600


async def test_over_limit_returns_exact_429_headers(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
) -> None:
    monkeypatch.setattr(rate_limit, "redis_client", FakeRedis([3, 417]))

    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit(
            _request(),
            operation=RateLimitOperation.COMMENT,
            target_type="project",
            target_id=PROJECT_ID,
        )

    assert error.value.status_code == 429
    assert error.value.detail == "Rate limit exceeded."
    assert error.value.headers == {
        "Retry-After": "417",
        "X-RateLimit-Limit": "2",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": error.value.headers["X-RateLimit-Reset"],
    }


async def test_operation_and_target_scopes_use_independent_keys(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
) -> None:
    redis = FakeRedis([1, 600])
    monkeypatch.setattr(rate_limit, "redis_client", redis)

    await rate_limit.enforce_rate_limit(
        _request(),
        operation=RateLimitOperation.COMMENT,
        target_type="project",
        target_id=PROJECT_ID,
    )
    await rate_limit.enforce_rate_limit(
        _request(),
        operation=RateLimitOperation.COMMENT,
        target_type="project",
        target_id=uuid4(),
    )
    await rate_limit.enforce_rate_limit(
        _request(),
        operation=RateLimitOperation.REPORT,
        target_type="comment",
        target_id=COMMENT_ID,
    )

    keys = [str(call[2][0]) for call in redis.calls]
    assert len(set(keys)) == 3
    assert ":comment:" in keys[0]
    assert ":report:" in keys[2]


async def test_different_origins_have_independent_hmac_identities(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
) -> None:
    redis = FakeRedis([1, 600])
    monkeypatch.setattr(rate_limit, "redis_client", redis)

    for origin in ("203.0.113.10", "203.0.113.11"):
        await rate_limit.enforce_rate_limit(
            _request(origin),
            operation=RateLimitOperation.COMMENT,
            target_type="project",
            target_id=PROJECT_ID,
        )

    first_key, second_key = str(redis.calls[0][2][0]), str(redis.calls[1][2][0])
    assert first_key != second_key
    assert "203.0.113.10" not in first_key
    assert "203.0.113.11" not in second_key


async def test_redis_failure_returns_503_without_bypass(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
) -> None:
    monkeypatch.setattr(rate_limit, "redis_client", FailingRedis())

    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit(
            _request(),
            operation=RateLimitOperation.UPLOAD,
            target_type="project",
            target_id=PROJECT_ID,
        )

    assert error.value.status_code == 503
    assert error.value.detail == "Rate limiting is temporarily unavailable."


@pytest.mark.parametrize(
    "malformed_result", [None, [], [1], ["1", 600], [0, 600], [1, -1]]
)
async def test_malformed_redis_result_returns_503(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
    malformed_result: object,
) -> None:
    redis = FakeRedis()
    redis.result = malformed_result  # type: ignore[assignment]
    monkeypatch.setattr(rate_limit, "redis_client", redis)

    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit(
            _request(),
            operation=RateLimitOperation.COMMENT,
            target_type="project",
            target_id=PROJECT_ID,
        )

    assert error.value.status_code == 503
    assert error.value.detail == "Rate limiting is temporarily unavailable."


async def test_fixed_window_expires_and_allows_a_later_request(
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_settings: None,
) -> None:
    clock = [100.0]
    redis = ClockedRedis(clock)
    monkeypatch.setattr(rate_limit, "redis_client", redis)
    monkeypatch.setattr(rate_limit.time, "time", lambda: clock[0])
    monkeypatch.setattr(rate_limit.settings, "rate_limit_comment_limit", 2)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_comment_window_seconds", 10)

    for _ in range(2):
        await rate_limit.enforce_rate_limit(
            _request(),
            operation=RateLimitOperation.COMMENT,
            target_type="project",
            target_id=PROJECT_ID,
        )
    clock[0] = 109.0
    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit(
            _request(),
            operation=RateLimitOperation.COMMENT,
            target_type="project",
            target_id=PROJECT_ID,
        )
    assert error.value.status_code == 429

    clock[0] = 110.0
    await rate_limit.enforce_rate_limit(
        _request(),
        operation=RateLimitOperation.COMMENT,
        target_type="project",
        target_id=PROJECT_ID,
    )


@pytest.mark.parametrize(
    ("route_module", "route_name", "kwargs"),
    [
        (
            comments_routes,
            "create_project_comment",
            {
                "project_id": PROJECT_ID,
                "payload": CitizenCommentCreateRequest(
                    author_id=uuid4(), content="A valid citizen comment."
                ),
            },
        ),
        (
            comments_routes,
            "report_project_comment",
            {
                "comment_id": COMMENT_ID,
                "payload": CommentReportCreateRequest(
                    reporter_id=uuid4(), reason="SPAM"
                ),
            },
        ),
    ],
)
async def test_comment_routes_apply_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
    route_module: object,
    route_name: str,
    kwargs: dict[str, object],
) -> None:
    limiter = AsyncMock()
    monkeypatch.setattr(route_module, "enforce_rate_limit", limiter)
    service_name = {
        "create_project_comment": "create_comment",
        "report_project_comment": "report_comment",
    }[route_name]
    service = AsyncMock(return_value=object())
    monkeypatch.setattr(route_module.service, service_name, service)

    route = getattr(route_module, route_name)
    await route(**kwargs, session=object(), request=_request())

    limiter.assert_awaited_once()
    service.assert_awaited_once()


async def test_rejected_comment_does_not_execute_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limiter = AsyncMock(
        side_effect=HTTPException(status_code=429, detail="Rate limit exceeded.")
    )
    service = AsyncMock()
    monkeypatch.setattr(comments_routes, "enforce_rate_limit", limiter)
    monkeypatch.setattr(comments_routes.service, "create_comment", service)

    with pytest.raises(HTTPException) as error:
        await comments_routes.create_project_comment(
            PROJECT_ID,
            CitizenCommentCreateRequest(
                author_id=uuid4(), content="A valid citizen comment."
            ),
            object(),
            _request(),
        )

    assert error.value.status_code == 429
    service.assert_not_awaited()


async def test_rejected_report_does_not_execute_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limiter = AsyncMock(
        side_effect=HTTPException(status_code=429, detail="Rate limit exceeded.")
    )
    service = AsyncMock()
    monkeypatch.setattr(comments_routes, "enforce_rate_limit", limiter)
    monkeypatch.setattr(comments_routes.service, "report_comment", service)

    with pytest.raises(HTTPException) as error:
        await comments_routes.report_project_comment(
            COMMENT_ID,
            CommentReportCreateRequest(reporter_id=uuid4(), reason="SPAM"),
            object(),
            _request(),
        )

    assert error.value.status_code == 429
    service.assert_not_awaited()


@pytest.mark.parametrize(
    "route_name",
    [
        "create_comment_evidence",
        "create_report_evidence_by_id",
        "create_project_evidence",
        "create_report_evidence",
    ],
)
async def test_all_evidence_upload_routes_apply_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
    route_name: str,
) -> None:
    limiter = AsyncMock()
    monkeypatch.setattr(evidence_routes, "enforce_rate_limit", limiter)
    service_name = {
        "create_comment_evidence": "upload_comment_evidence",
        "create_report_evidence_by_id": "upload_report_evidence_by_id",
        "create_project_evidence": "upload_project_evidence",
        "create_report_evidence": "upload_report_evidence",
    }[route_name]
    monkeypatch.setattr(
        evidence_routes.service,
        service_name,
        AsyncMock(return_value=object()),
    )
    route = getattr(evidence_routes, route_name)
    kwargs: dict[str, object] = {
        "session": object(),
        "request": _request(),
        "uploader_id": uuid4(),
        "file": object(),
    }
    if route_name == "create_report_evidence":
        kwargs["project_id"] = PROJECT_ID
        kwargs["report_id"] = REPORT_ID
    elif route_name == "create_report_evidence_by_id":
        kwargs["report_id"] = REPORT_ID
    elif route_name == "create_project_evidence":
        kwargs["project_id"] = PROJECT_ID
    else:
        kwargs["comment_id"] = COMMENT_ID

    await route(**kwargs)
    limiter.assert_awaited_once()


async def test_rejected_upload_does_not_execute_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limiter = AsyncMock(
        side_effect=HTTPException(status_code=429, detail="Rate limit exceeded.")
    )
    service = AsyncMock()
    monkeypatch.setattr(evidence_routes, "enforce_rate_limit", limiter)
    monkeypatch.setattr(evidence_routes.service, "upload_project_evidence", service)

    with pytest.raises(HTTPException) as error:
        await evidence_routes.create_project_evidence(
            PROJECT_ID,
            object(),
            _request(),
            uuid4(),
            None,
            object(),
        )

    assert error.value.status_code == 429
    service.assert_not_awaited()
