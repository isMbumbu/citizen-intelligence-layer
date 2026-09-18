"""Version-one API router registration."""

from fastapi import APIRouter

from app.api.v1.modules.civic_action.routes import report_router as civic_report_router
from app.api.v1.modules.civic_action.routes import router as civic_action_router
from app.api.v1.modules.comments.routes import router as comments_router
from app.api.v1.modules.evidence.routes import router as evidence_router
from app.api.v1.modules.moderation.routes import router as moderation_router
from app.api.v1.modules.projects.routes import router as projects_router
from app.api.v1.modules.taxonomy.routes import router as taxonomy_router

api_router = APIRouter()

api_router.include_router(projects_router)
api_router.include_router(taxonomy_router)
api_router.include_router(civic_action_router)
api_router.include_router(civic_report_router)
api_router.include_router(comments_router)
api_router.include_router(evidence_router)
api_router.include_router(moderation_router)
