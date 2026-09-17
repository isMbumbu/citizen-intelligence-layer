"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "citizen_intelligence",
    broker=settings.rabbitmq_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    result_serializer="json",
    task_publish_retry=True,
    task_serializer="json",
    task_track_started=True,
    worker_concurrency=settings.celery_worker_concurrency,
    worker_prefetch_multiplier=1,
)
celery_app.conf.imports = ("app.tasks.health",)
