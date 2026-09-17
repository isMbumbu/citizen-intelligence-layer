"""Safe API error responses."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    """Register client-safe handlers that do not leak internal error details."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info(
            "Request validation failed",
            extra={"path": request.url.path, "errors": len(exc.errors())},
        )
        return JSONResponse(
            status_code=422,
            content={"detail": "Request validation failed."},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled request error",
            extra={"path": request.url.path, "exception_type": type(exc).__name__},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred."},
        )
