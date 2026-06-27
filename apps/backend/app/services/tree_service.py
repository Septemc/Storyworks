from __future__ import annotations

from fastapi import HTTPException

from ..database import db


ALLOWED_TREE_TABLES = {"worldbook_categories", "scripts"}


def normalize_parent_id(parent_id):
    return parent_id or None


def validate_parent_link(project_id: str, table: str, node_id: str, parent_id, *, pending_parents: dict[str, str | None] | None = None):
    if table not in ALLOWED_TREE_TABLES:
        raise ValueError(f"Unsupported tree table: {table}")

    normalized_parent = normalize_parent_id(parent_id)
    if normalized_parent is None:
        return None
    if normalized_parent == node_id:
        raise HTTPException(status_code=400, detail="父级不能指向自身")

    pending = pending_parents or {}
    parent_exists = db.one(f"SELECT id FROM {table} WHERE project_id = ? AND id = ?", (project_id, normalized_parent))
    if not parent_exists:
        raise HTTPException(status_code=400, detail="父级不存在或不属于当前项目")

    seen: set[str] = set()
    cursor = normalized_parent
    while cursor:
        if cursor == node_id:
            raise HTTPException(status_code=400, detail="父级不能指向自己的子级")
        if cursor in seen:
            raise HTTPException(status_code=400, detail="父级层级存在循环")
        seen.add(cursor)
        if cursor in pending:
            cursor = pending[cursor]
            continue
        row = db.one(f"SELECT parent_id FROM {table} WHERE project_id = ? AND id = ?", (project_id, cursor))
        cursor = normalize_parent_id(row.get("parent_id")) if row else None
    return normalized_parent


def validate_batch_parent_links(project_id: str, table: str, rows: list[dict]):
    pending: dict[str, str | None] = {}
    for row in rows:
        node_id = row.get("id")
        if not node_id:
            raise HTTPException(status_code=400, detail="缺少节点 ID")
        exists = db.one(f"SELECT id FROM {table} WHERE project_id = ? AND id = ?", (project_id, node_id))
        if not exists:
            raise HTTPException(status_code=404, detail="节点不存在")
        pending[node_id] = normalize_parent_id(row.get("parent_id"))

    for row in rows:
        validate_parent_link(project_id, table, row["id"], row.get("parent_id"), pending_parents=pending)
    return pending
