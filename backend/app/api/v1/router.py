"""Version-one API router registration."""

from fastapi import APIRouter

from app.api.v1.modules.civic_action.routes import router as civic_action_router
from app.api.v1.modules.projects.routes import router as projects_router

api_router = APIRouter()

api_router.include_router(projects_router)
api_router.include_router(civic_action_router)
