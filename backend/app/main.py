"""FastAPI application entry point."""

import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_database, get_session
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, logger
from app.core.readiness import ReadinessReport, get_readiness_report
from app.core.redis import close_redis
from app.core.security import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Set up process concerns and release database resources on shutdown."""
    configure_logging()
    logger.info("Application started", extra={"event": "application_started"})
    try:
        yield
    finally:
        await close_redis()
        await close_database()
        logger.info("Application stopped", extra={"event": "application_stopped"})


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
register_exception_handlers(app)


@app.middleware("http")
async def log_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log request metadata without recording request bodies or credentials."""
    started_at = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "Request completed",
        extra={
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
    )
    return response


@app.get("/health", tags=["health"], summary="Liveness check")
async def health_check() -> dict[str, str]:
    """Report that the API process is accepting requests."""
    return {"status": "ok"}


@app.get(
    "/health/ready",
    tags=["health"],
    summary="Database and cache readiness check",
)
async def readiness_check(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReadinessReport:
    """Verify the API can reach PostgreSQL and Redis asynchronously."""
    report = await get_readiness_report(session)
    if report.status == "not_ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=report.model_dump(mode="json"),
        )
    return report


app.include_router(api_router, prefix=settings.api_v1_prefix)
