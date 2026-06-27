from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from shared.config import config

from ..database import now


router = APIRouter(prefix="/api")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("/health")
def health():
    return ok(
        {
            "status": "ok",
            "time": now(),
            "features": {
                "ai_settings": True,
                "llm_config_persistence": True,
                "schema_migrations": True,
            },
        }
    )


@router.get("/settings/ai")
def ai_settings():
    return ok(config.public_ai_config())


@router.put("/settings/ai")
def update_ai_settings(data: dict = Body(...)):
    try:
        updated = config.update_ai_config(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok(updated, "AI 配置已保存")
