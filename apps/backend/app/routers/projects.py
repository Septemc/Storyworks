from __future__ import annotations

from fastapi import APIRouter, Body, Query

from ..services.consistency_service import project_consistency_report, repair_project_consistency
from ..services.ai_log_service import apply_ai_log_result
from ..services.import_service import import_project_package, validate_project_package
from ..services.project_service import (
    build_project_export,
    create_project_payload,
    delete_project_payload,
    list_projects,
    project_ai_logs,
    project_overview,
    reset_demo_project_payload,
    serialize_project,
    update_project_payload,
    update_project_status,
)
from ..database import project_or_404


router = APIRouter(prefix="/api/projects")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("")
def projects(include_archived: bool = False):
    return ok(list_projects(include_archived))


@router.post("")
def create_project(data: dict = Body(...)):
    return ok(create_project_payload(data), "项目创建成功")


@router.post("/import/preview")
def preview_project_import(data: dict = Body(...)):
    return ok(validate_project_package(data), "导入预览完成")


@router.post("/import")
def import_project(data: dict = Body(...)):
    return ok(import_project_package(data), "项目导入完成")


@router.get("/{project_id}")
def get_project(project_id: str):
    return ok(serialize_project(project_or_404(project_id)))


@router.get("/{project_id}/export")
def export_project(project_id: str):
    return ok(build_project_export(project_id), "项目导出完成")


@router.put("/{project_id}")
def update_project(project_id: str, data: dict = Body(...)):
    return ok(update_project_payload(project_id, data), "项目更新成功")


@router.post("/{project_id}/archive")
def archive_project(project_id: str, data: dict = Body(default={})):
    archived = bool(data.get("archived", True))
    return ok(update_project_status(project_id, "archived" if archived else "active"), "项目已归档" if archived else "项目已恢复")


@router.post("/{project_id}/demo/reset")
def reset_demo_project(project_id: str):
    return ok(reset_demo_project_payload(project_id), "Demo 项目已重置")


@router.delete("/{project_id}")
def delete_project(project_id: str, data: dict = Body(default={})):
    delete_project_payload(project_id, data.get("confirm_name"))
    return ok(None, "项目删除成功")


@router.get("/{project_id}/overview")
def overview(project_id: str):
    return ok(project_overview(project_id))


@router.get("/{project_id}/ai/logs")
def ai_logs(project_id: str, target_type: str = "", target_id: str = "", limit: int = Query(50, ge=1, le=200)):
    return ok(project_ai_logs(project_id, target_type, target_id, limit))


@router.post("/{project_id}/ai/logs/{log_id}/apply")
def apply_ai_log(project_id: str, log_id: str):
    return ok(apply_ai_log_result(project_id, log_id), "AI 历史已应用")


@router.get("/{project_id}/consistency/check")
def consistency_check(project_id: str):
    project_or_404(project_id)
    return ok(project_consistency_report(project_id), "一致性检查完成")


@router.post("/{project_id}/consistency/repair")
def consistency_repair(project_id: str):
    project_or_404(project_id)
    return ok(repair_project_consistency(project_id), "一致性修复完成")
