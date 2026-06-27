from __future__ import annotations

from fastapi import APIRouter, Body

from ..services.character_service import (
    build_character_graph,
    create_character_payload,
    create_character_relation_payload,
    delete_character_payload,
    delete_character_relation_payload,
    export_characters,
    get_character_detail,
    list_characters,
    list_character_relations,
    update_character_payload,
)


router = APIRouter(prefix="/api/projects/{project_id}")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("/characters")
def characters(project_id: str, q: str = "", character_type: str = "", status: str = "", tag: str = ""):
    return ok(list_characters(project_id, q=q, character_type=character_type, status=status, tag=tag))


@router.post("/characters")
def create_character(project_id: str, data: dict = Body(...)):
    return ok(create_character_payload(project_id, data), "角色创建成功")


@router.get("/characters/detail/{character_id}")
def character(project_id: str, character_id: str):
    return ok(get_character_detail(project_id, character_id))


@router.put("/characters/{character_id}")
def update_character(project_id: str, character_id: str, data: dict = Body(...)):
    return ok(update_character_payload(project_id, character_id, data), "角色更新成功")


@router.delete("/characters/{character_id}")
def delete_character(project_id: str, character_id: str):
    delete_character_payload(project_id, character_id)
    return ok(None, "角色删除成功")


@router.get("/characters/relations/all")
def character_relations(project_id: str):
    return ok(list_character_relations(project_id))


@router.post("/characters/relations")
def create_character_relation(project_id: str, data: dict = Body(...)):
    return ok(create_character_relation_payload(project_id, data), "关系创建成功")


@router.delete("/characters/relations/{relation_id}")
def delete_character_relation(project_id: str, relation_id: str):
    delete_character_relation_payload(project_id, relation_id)
    return ok(None, "关系删除成功")


@router.get("/characters/graph")
def character_graph(project_id: str):
    return ok(build_character_graph(project_id))


@router.get("/characters/export")
def export_characters_route(project_id: str, format: str = "markdown", ids: str = ""):
    return ok(export_characters(project_id, format, ids))
