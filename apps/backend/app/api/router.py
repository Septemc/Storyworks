from fastapi import APIRouter

from app.api.routes.characters import router as characters_router
from app.api.routes.health import router as health_router
from app.api.routes.presets import router as presets_router
from app.api.routes.projects import router as projects_router
from app.api.routes.scripts import router as scripts_router
from app.api.routes.worldbook import router as worldbook_router

api_router = APIRouter(prefix="/api")
api_router.include_router(characters_router)
api_router.include_router(health_router)
api_router.include_router(presets_router)
api_router.include_router(projects_router)
api_router.include_router(scripts_router)
api_router.include_router(worldbook_router)
