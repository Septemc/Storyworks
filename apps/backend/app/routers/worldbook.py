from __future__ import annotations

from fastapi import APIRouter, Body

from ..services.worldbook_service import (
    build_worldbook_graph,
    create_worldbook_entry_payload,
    create_worldbook_category,
    create_worldbook_relation_payload,
    delete_worldbook_entry_payload,
    delete_worldbook_category,
    delete_worldbook_relation_payload,
    export_worldbook,
    get_worldbook_entry_detail,
    list_worldbook_entries,
    list_worldbook_categories,
    list_worldbook_relations,
    sort_worldbook_categories,
    update_worldbook_entry_payload,
    update_worldbook_category,
)


router = APIRouter(prefix="/api/projects/{project_id}/worldbook")


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


@router.get("/categories")
def worldbook_categories(project_id: str):
    return ok(list_worldbook_categories(project_id))


@router.post("/categories")
def create_category(project_id: str, data: dict = Body(...)):
    return ok(create_worldbook_category(project_id, data), "分类创建成功")


@router.put("/categories/{category_id}")
def update_category(project_id: str, category_id: str, data: dict = Body(...)):
    return ok(update_worldbook_category(project_id, category_id, data), "分类更新成功")


@router.delete("/categories/{category_id}")
def delete_category(project_id: str, category_id: str):
    delete_worldbook_category(project_id, category_id)
    return ok(None, "分类删除成功")


@router.patch("/categories/sort")
def sort_categories(project_id: str, data: list[dict] = Body(...)):
    return ok(sort_worldbook_categories(project_id, data), "分类排序已保存")


@router.get("/entries")
def worldbook_entries(project_id: str, category_id: str | None = None, status: str | None = None, q: str = "", tag: str = "", min_importance: int = 1):
    return ok(list_worldbook_entries(project_id, category_id=category_id, status=status, q=q, tag=tag, min_importance=min_importance))


@router.post("/entries")
def create_worldbook_entry(project_id: str, data: dict = Body(...)):
    return ok(create_worldbook_entry_payload(project_id, data), "条目创建成功")


@router.get("/entries/{entry_id}")
def worldbook_entry(project_id: str, entry_id: str):
    return ok(get_worldbook_entry_detail(project_id, entry_id))


@router.put("/entries/{entry_id}")
def update_worldbook_entry(project_id: str, entry_id: str, data: dict = Body(...)):
    return ok(update_worldbook_entry_payload(project_id, entry_id, data), "条目更新成功")


@router.delete("/entries/{entry_id}")
def delete_worldbook_entry(project_id: str, entry_id: str):
    delete_worldbook_entry_payload(project_id, entry_id)
    return ok(None, "条目删除成功")


@router.get("/relations")
def worldbook_relations(project_id: str):
    return ok(list_worldbook_relations(project_id))


@router.post("/relations")
def create_worldbook_relation(project_id: str, data: dict = Body(...)):
    return ok(create_worldbook_relation_payload(project_id, data), "关联创建成功")


@router.delete("/relations/{relation_id}")
def delete_worldbook_relation(project_id: str, relation_id: str):
    delete_worldbook_relation_payload(project_id, relation_id)
    return ok(None, "关联删除成功")


@router.get("/graph")
def worldbook_graph(project_id: str, category_id: str | None = None, min_importance: int = 1):
    return ok(build_worldbook_graph(project_id, category_id=category_id, min_importance=min_importance))


@router.get("/export")
def export_worldbook_route(project_id: str, format: str = "markdown", ids: str = ""):
    return ok(export_worldbook(project_id, format, ids))
