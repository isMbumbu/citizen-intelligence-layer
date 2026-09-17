"""Minimal worker task used to confirm broker and worker wiring."""

from app.tasks.celery_app import celery_app


@celery_app.task(name="system.ping")
def ping() -> str:
    """Return a deterministic result without performing business work."""
    return "pong"
