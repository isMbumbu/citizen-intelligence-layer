"""Celery entry point for service-owned evidence processing."""

import asyncio
from uuid import UUID

from app.api.v1.modules.evidence.service import process_evidence
from app.core.database import async_session_maker
from app.core.logging import logger
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="evidence.process")  # type: ignore[untyped-decorator]
def process_evidence_task(task: object, evidence_id: str) -> str:
    """Process evidence by identifier and delegate all rules to the service."""
    task_id = getattr(getattr(task, "request", None), "id", None)
    logger.info("Starting evidence processing evidence_id=%s", evidence_id)

    async def run() -> str:
        async with async_session_maker() as session:
            state = await process_evidence(
                session,
                UUID(evidence_id),
                task_id=task_id,
            )
            return state.value

    try:
        return asyncio.run(run())
    except Exception:
        logger.exception("Evidence processing task failed evidence_id=%s", evidence_id)
        raise
