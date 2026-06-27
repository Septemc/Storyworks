from __future__ import annotations

from fastapi import APIRouter, Body

from ..services.script_service import (
    add_script_reference_payload,
    build_script_tree,
    create_script_payload,
    delete_script_payload,
    delete_script_reference_payload,
    export_scripts,
    get_script_detail,
    list_scripts,
    referenced_by,
    update_script_payload,
)


router = APIRouter(prefix="/api/projects/{project_id}")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("/scripts")
def scripts(project_id: str, node_type: str = "", status: str = "", q: str = ""):
    return ok(list_scripts(project_id, node_type=node_type, status=status, q=q))


@router.get("/scripts/tree")
def script_tree(project_id: str):
    return ok(build_script_tree(project_id))


@router.post("/scripts")
def create_script(project_id: str, data: dict = Body(...)):
    return ok(create_script_payload(project_id, data), "节点创建成功")


@router.get("/scripts/detail/{script_id}")
def script(project_id: str, script_id: str):
    return ok(get_script_detail(project_id, script_id))


@router.put("/scripts/{script_id}")
def update_script(project_id: str, script_id: str, data: dict = Body(...)):
    return ok(update_script_payload(project_id, script_id, data), "节点更新成功")


@router.delete("/scripts/{script_id}")
def delete_script(project_id: str, script_id: str):
    delete_script_payload(project_id, script_id)
    return ok(None, "节点删除成功")


@router.post("/scripts/{script_id}/references")
def add_script_reference(project_id: str, script_id: str, data: dict = Body(...)):
    return ok(add_script_reference_payload(project_id, script_id, data), "引用已添加")


@router.delete("/scripts/references/{reference_id}")
def delete_script_reference(project_id: str, reference_id: str):
    delete_script_reference_payload(project_id, reference_id)
    return ok(None, "引用已删除")


@router.get("/references/{ref_type}/{ref_id}")
def referenced_by_route(project_id: str, ref_type: str, ref_id: str):
    return ok(referenced_by(project_id, ref_type, ref_id))


@router.get("/scripts/export")
def export_scripts_route(project_id: str, format: str = "markdown"):
    return ok(export_scripts(project_id, format))
