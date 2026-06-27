from __future__ import annotations

from fastapi import APIRouter

from ..services.version_service import list_versions, restore_version_payload, version_diff_payload


router = APIRouter(prefix="/api/projects/{project_id}")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("/versions/{entity_type}/{entity_id}")
def versions(project_id: str, entity_type: str, entity_id: str):
    return ok(list_versions(project_id, entity_type, entity_id))


@router.get("/version-diff/{version_id}")
def version_diff(project_id: str, version_id: str):
    return ok(version_diff_payload(project_id, version_id), "版本差异已生成")


@router.post("/versions/{version_id}/restore")
def restore_version(project_id: str, version_id: str):
    return ok(restore_version_payload(project_id, version_id), "版本已恢复")
