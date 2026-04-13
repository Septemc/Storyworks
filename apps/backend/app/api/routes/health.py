from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
    }
