"""Redis-backed request rate limiting for abuse-prone write operations."""

import hashlib
import hmac
import time
from enum import StrEnum
from uuid import UUID

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import logger
from app.core.redis import redis_client

_FIXED_WINDOW_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


class RateLimitOperation(StrEnum):
    COMMENT = "comment"
    REPORT = "report"
    UPLOAD = "upload"


async def enforce_rate_limit(
    request: Request,
    *,
    operation: RateLimitOperation,
    target_type: str,
    target_id: UUID,
) -> None:
    """Enforce one target-scoped fixed-window rate limit."""
    limit, window_seconds = _configuration(operation)
    identity = _identity_digest(request)
    window = int(time.time()) // window_seconds
    if operation is RateLimitOperation.UPLOAD:
        key = (
            f"{settings.rate_limit_key_prefix}:{operation.value}:"
            f"{identity}:{target_type}:{target_id}:{window}"
        )
    else:
        key = (
            f"{settings.rate_limit_key_prefix}:{operation.value}:"
            f"{identity}:{target_id}:{window}"
        )
    reset_at = (window + 1) * window_seconds
    try:
        result = await redis_client.eval(
            _FIXED_WINDOW_SCRIPT,
            1,
            key,
            window_seconds,
        )
    except RedisError as error:
        logger.error(
            "Rate-limit dependency unavailable operation=%s error_type=%s",
            operation,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting is temporarily unavailable.",
        ) from error

    try:
        count, ttl = _parse_result(result)
    except (TypeError, ValueError) as error:
        logger.error(
            "Rate-limit dependency returned an invalid result operation=%s "
            "error_type=%s",
            operation,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting is temporarily unavailable.",
        ) from error
    ttl = max(ttl, 1)
    if count <= limit:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded.",
        headers={
            "Retry-After": str(ttl),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_at),
        },
    )


def _parse_result(result: object) -> tuple[int, int]:
    """Validate the two integer values returned by the limiter Lua script."""
    if not isinstance(result, (list, tuple)) or len(result) != 2:
        raise ValueError("Unexpected rate-limit result shape.")
    count, ttl = result
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or isinstance(ttl, bool)
        or not isinstance(ttl, int)
        or count < 1
        or ttl < 0
    ):
        raise ValueError("Unexpected rate-limit result values.")
    return count, ttl


def _configuration(operation: RateLimitOperation) -> tuple[int, int]:
    """Return the configured limit and window for one operation."""
    configurations = {
        RateLimitOperation.COMMENT: (
            settings.rate_limit_comment_limit,
            settings.rate_limit_comment_window_seconds,
        ),
        RateLimitOperation.REPORT: (
            settings.rate_limit_report_limit,
            settings.rate_limit_report_window_seconds,
        ),
        RateLimitOperation.UPLOAD: (
            settings.rate_limit_upload_limit,
            settings.rate_limit_upload_window_seconds,
        ),
    }
    return configurations[operation]


def _identity_digest(request: Request) -> str:
    """Return a keyed identity digest without persisting the raw origin."""
    actor_id = getattr(getattr(request, "state", None), "actor_id", None)
    identity = str(actor_id) if actor_id is not None else _client_origin(request)
    return hmac.new(
        settings.rate_limit_identity_secret.encode(),
        identity.encode(),
        hashlib.sha256,
    ).hexdigest()


def _client_origin(request: Request) -> str:
    """Return only the immediate ASGI client origin, never forwarded headers."""
    return request.client.host if request.client is not None else "unknown"
