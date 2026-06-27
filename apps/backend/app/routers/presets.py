from __future__ import annotations

from fastapi import APIRouter, Body

from ..services.preset_service import (
    apply_preset_payload,
    combine_presets_payload,
    create_preset_payload,
    delete_preset_payload,
    ensure_preset,
    export_presets,
    list_presets,
    update_preset_payload,
)


router = APIRouter(prefix="/api/projects/{project_id}/presets")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("")
def presets(project_id: str, category: str = "", q: str = ""):
    return ok(list_presets(project_id, category=category, q=q))


@router.post("")
def create_preset(project_id: str, data: dict = Body(...)):
    return ok(create_preset_payload(project_id, data), "预设创建成功")


@router.get("/detail/{preset_id}")
def preset(project_id: str, preset_id: str):
    return ok(ensure_preset(project_id, preset_id))


@router.put("/{preset_id}")
def update_preset(project_id: str, preset_id: str, data: dict = Body(...)):
    return ok(update_preset_payload(project_id, preset_id, data), "预设更新成功")


@router.delete("/{preset_id}")
def delete_preset(project_id: str, preset_id: str):
    delete_preset_payload(project_id, preset_id)
    return ok(None, "预设删除成功")


@router.post("/apply")
def apply_preset(project_id: str, data: dict = Body(...)):
    return ok(apply_preset_payload(project_id, data), "预设已应用")


@router.post("/combine")
def combine_presets(project_id: str, data: dict = Body(...)):
    return ok(combine_presets_payload(project_id, data), "预设组合完成")


@router.get("/export")
def export_presets_route(project_id: str, format: str = "json"):
    return ok(export_presets(project_id, format))
