"""Structured application logging setup."""

import json
import logging
from typing import Any

from app.core.config import settings

_SAFE_CONTEXT_FIELDS = frozenset(
    {
        "dependency",
        "duration_ms",
        "error_type",
        "errors",
        "event",
        "exception_type",
        "method",
        "path",
        "status_code",
    }
)


class StructuredFormatter(logging.Formatter):
    """Emit request-safe JSON logs with selected operational context."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize only reviewed context keys, never arbitrary log extras."""
        context = {
            field: record.__dict__[field]
            for field in _SAFE_CONTEXT_FIELDS
            if field in record.__dict__
        }
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if context:
            payload["context"] = context
        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging() -> None:
    """Configure process logging without recording secrets or request bodies."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    if not root_logger.handlers:
        root_logger.addHandler(logging.StreamHandler())
    formatter = StructuredFormatter()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)


logger = logging.getLogger("citizen_intelligence")
