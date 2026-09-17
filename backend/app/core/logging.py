"""Structured application logging setup."""

import logging

from app.core.config import settings


def configure_logging() -> None:
    """Configure process logging without recording secrets or request bodies."""
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


logger = logging.getLogger("citizen_intelligence")
