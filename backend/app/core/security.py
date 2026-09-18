"""Security-oriented ASGI middleware and moderation auth boundary."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MODERATE_CONTENT_PERMISSION = "moderate_content"


@dataclass(frozen=True)
class CurrentModerator:
    """Trusted actor context supplied by the eventual authentication layer."""

    actor_id: UUID
    permissions: frozenset[str]


async def get_current_moderator() -> CurrentModerator:
    """Fail closed until a production authentication provider is integrated."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required.",
    )


async def get_authorized_moderator(
    actor: Annotated[CurrentModerator, Depends(get_current_moderator)],
) -> CurrentModerator:
    """Resolve a trusted actor and enforce moderation permission."""
    return require_moderation_permission(actor)


def require_moderation_permission(actor: CurrentModerator) -> CurrentModerator:
    """Require the explicit permission for content moderation operations."""
    if MODERATE_CONTENT_PERMISSION not in actor.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderation permission is required.",
        )
    return actor


class SecurityHeadersMiddleware:
    """Attach secure response defaults appropriate for an API."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def add_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"cache-control", b"no-store"),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, add_security_headers)
