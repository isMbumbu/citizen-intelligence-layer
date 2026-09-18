"""Security-oriented ASGI middleware and minimal trusted-actor authorization."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MODERATE_CONTENT_PERMISSION = "moderate_content"
EVIDENCE_READ_PROTECTED_PERMISSION = "evidence_read_protected"


@dataclass(frozen=True)
class CurrentModerator:
    """Trusted actor context supplied by the eventual authentication layer."""

    actor_id: UUID
    permissions: frozenset[str]


CurrentActor = CurrentModerator


async def get_current_moderator() -> CurrentModerator:
    """Fail closed until a production authentication provider is integrated."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required.",
    )


async def get_optional_current_actor() -> CurrentModerator | None:
    """Return an optional trusted actor without creating a broader auth system."""
    try:
        return await get_current_moderator()
    except HTTPException as error:
        if error.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


async def get_authorized_moderator(
    actor: Annotated[CurrentModerator, Depends(get_current_moderator)],
) -> CurrentModerator:
    """Resolve a trusted actor and enforce moderation permission."""
    return require_moderation_permission(actor)


async def get_authorized_evidence_reader(
    actor: Annotated[CurrentModerator, Depends(get_current_moderator)],
) -> CurrentModerator:
    """Resolve a trusted actor and enforce minimum protected-evidence permission."""
    return require_evidence_read_protected_permission(actor)


def require_permission(
    actor: CurrentModerator,
    permission: str,
    *,
    detail: str,
) -> CurrentModerator:
    """Require a specific explicit permission for a protected operation."""
    if permission not in actor.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
    return actor


def require_moderation_permission(actor: CurrentModerator) -> CurrentModerator:
    """Require the explicit permission for content moderation operations."""
    return require_permission(
        actor,
        MODERATE_CONTENT_PERMISSION,
        detail="Moderation permission is required.",
    )


def require_evidence_read_protected_permission(
    actor: CurrentModerator,
) -> CurrentModerator:
    """Require the explicit permission for protected evidence retrieval."""
    return require_permission(
        actor,
        EVIDENCE_READ_PROTECTED_PERMISSION,
        detail="Protected evidence permission is required.",
    )


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
