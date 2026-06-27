from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from ..database import db, new_id, now, parse_json, project_or_404, record_version, to_json, to_json_array
from .ai_service import clean_text, record_ai_operation
from .export_service import export_worldbook_payload
from .tree_service import validate_batch_parent_links, validate_parent_link


WORLD_ENTRY_JSON_FIELDS = {"structured_data": {}, "tags": [], "ai_metadata": {}}
CATEGORY_JSON_FIELDS = {"template": {"sections": []}, "custom_fields": []}


def parse_row_fields(row: dict | None, fields: dict[str, Any]) -> dict | None:
    if not row:
        return None
    for key, default in fields.items():
        row[key] = parse_json(row.get(key), default)
    return row


def require_row(row: dict | None, message: str) -> dict:
    if row is None:
        raise HTTPException(status_code=404, detail=message)
    return row


def create_version_snapshot(project_id: str, entity_type: str, entity_id: str, row: dict, summary: str = "") -> None:
    version = int(row.get("version") or 1)
    record_version(project_id, entity_type, entity_id, version, row, summary)


def record_ai_apply_metadata(project_id: str, target_type: str, target_id: str, data: dict, applied_result: Any) -> None:
    meta = data.get("ai_apply")
    if not isinstance(meta, dict):
        return
    record_ai_operation(
        project_id,
        target_type,
        "apply",
        str(meta.get("prompt") or ""),
        meta.get("result", applied_result),
        target_id=target_id,
        section=clean_text(meta.get("section")),
        field=clean_text(meta.get("field")),
        instruction=clean_text(meta.get("instruction")),
        request=meta.get("request") if isinstance(meta.get("request"), dict) else {},
        process_log=meta.get("process_log") if isinstance(meta.get("process_log"), list) else [],
    )


def ai_update_summary(data: dict, fallback: str) -> str:
    if data.get("_version_summary"):
        return str(data.get("_version_summary"))
    if data.get("summary"):
        return str(data.get("summary"))
    meta = data.get("ai_apply")
    if isinstance(meta, dict):
        target = " / ".join(item for item in [clean_text(meta.get("section")), clean_text(meta.get("field"))] if item)
        return f"AI迭代 {target or '全文'}"
    return fallback


def validate_category(project_id: str, category_id: Any) -> str | None:
    normalized = clean_text(category_id)
    if not normalized:
        return None
    require_row(db.one("SELECT id FROM worldbook_categories WHERE project_id = ? AND id = ?", (project_id, normalized)), "分类不存在")
    return normalized


def list_worldbook_categories(project_id: str) -> list[dict]:
    rows = db.all(
        "SELECT * FROM worldbook_categories WHERE project_id = ? ORDER BY parent_id IS NOT NULL, sort_order, name",
        (project_id,),
    )
    return [parse_row_fields(row, CATEGORY_JSON_FIELDS) for row in rows]


def create_worldbook_category(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    stamp = now()
    category_id = new_id("cat")
    parent_id = validate_parent_link(project_id, "worldbook_categories", category_id, data.get("parent_id"))
    db.exec(
        """INSERT INTO worldbook_categories (id, project_id, parent_id, name, description, template, custom_fields, sort_order, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            category_id,
            project_id,
            parent_id,
            clean_text(data.get("name"), "未命名分类"),
            data.get("description", ""),
            to_json(data.get("template") or {"sections": []}),
            to_json_array(data.get("custom_fields")),
            int(data.get("sort_order") or 0),
            stamp,
            stamp,
        ),
    )
    return parse_row_fields(db.one("SELECT * FROM worldbook_categories WHERE id = ?", (category_id,)), {"template": {}, "custom_fields": []})


def update_worldbook_category(project_id: str, category_id: str, data: dict) -> dict:
    project_or_404(project_id)
    if not db.one("SELECT id FROM worldbook_categories WHERE project_id = ? AND id = ?", (project_id, category_id)):
        raise HTTPException(status_code=404, detail="分类不存在")
    fields, params = [], []
    mapping = {"parent_id": "parent_id", "name": "name", "description": "description", "sort_order": "sort_order"}
    for key, col in mapping.items():
        if key in data:
            fields.append(f"{col} = ?")
            params.append(validate_parent_link(project_id, "worldbook_categories", category_id, data.get(key)) if key == "parent_id" else data.get(key))
    if "template" in data:
        fields.append("template = ?")
        params.append(to_json(data.get("template") or {"sections": []}))
    if "custom_fields" in data:
        fields.append("custom_fields = ?")
        params.append(to_json_array(data.get("custom_fields")))
    if fields:
        fields.append("updated_at = ?")
        params.extend([now(), project_id, category_id])
        db.exec(f"UPDATE worldbook_categories SET {', '.join(fields)} WHERE project_id = ? AND id = ?", tuple(params))
    return parse_row_fields(db.one("SELECT * FROM worldbook_categories WHERE id = ?", (category_id,)), {"template": {}, "custom_fields": []})


def delete_worldbook_category(project_id: str, category_id: str) -> None:
    project_or_404(project_id)
    db.exec("UPDATE worldbook_entries SET category_id = NULL WHERE project_id = ? AND category_id = ?", (project_id, category_id))
    deleted = db.exec("DELETE FROM worldbook_categories WHERE project_id = ? AND id = ?", (project_id, category_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="分类不存在")


def sort_worldbook_categories(project_id: str, data: list[dict]) -> list[dict]:
    project_or_404(project_id)
    stamp = now()
    pending = validate_batch_parent_links(project_id, "worldbook_categories", data)
    for item in data:
        db.exec(
            "UPDATE worldbook_categories SET parent_id = ?, sort_order = ?, updated_at = ? WHERE project_id = ? AND id = ?",
            (pending[item["id"]], int(item.get("sort_order") or 0), stamp, project_id, item.get("id")),
        )
    return list_worldbook_categories(project_id)


def get_worldbook_entry(project_id: str, entry_id: str) -> dict | None:
    row = db.one("SELECT * FROM worldbook_entries WHERE project_id = ? AND id = ?", (project_id, entry_id))
    return parse_row_fields(row, WORLD_ENTRY_JSON_FIELDS)


def ensure_worldbook_entry(project_id: str, entry_id: str) -> dict:
    return require_row(get_worldbook_entry(project_id, entry_id), "世界书条目不存在")


def list_worldbook_entries(
    project_id: str,
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    q: str = "",
    tag: str = "",
    min_importance: int = 1,
) -> list[dict]:
    project_or_404(project_id)
    sql = "SELECT * FROM worldbook_entries WHERE project_id = ? AND importance >= ?"
    params: list[Any] = [project_id, int(min_importance or 1)]
    if category_id:
        sql += " AND category_id = ?"
        params.append(category_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if q:
        sql += " AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if tag:
        sql += " AND tags LIKE ?"
        params.append(f"%{tag}%")
    sql += " ORDER BY updated_at DESC"
    return [parse_row_fields(row, WORLD_ENTRY_JSON_FIELDS) for row in db.all(sql, tuple(params))]


def create_worldbook_entry_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    title = clean_text(data.get("title"))
    if not title:
        raise HTTPException(status_code=400, detail="条目标题不能为空")
    category_id = validate_category(project_id, data.get("category_id"))
    stamp = now()
    entry_id = new_id("world")
    db.exec(
        """INSERT INTO worldbook_entries
           (id, project_id, category_id, title, content, structured_data, importance, visibility, status, tags, creator, ai_generated, ai_prompt, ai_metadata, version, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (
            entry_id,
            project_id,
            category_id,
            title,
            data.get("content", ""),
            to_json(data.get("structured_data")),
            int(data.get("importance") or 3),
            data.get("visibility", "public"),
            data.get("status", "draft"),
            to_json_array(data.get("tags")),
            data.get("creator", ""),
            1 if data.get("ai_generated") else 0,
            data.get("ai_prompt", ""),
            to_json(data.get("ai_metadata")),
            stamp,
            stamp,
        ),
    )
    row = ensure_worldbook_entry(project_id, entry_id)
    create_version_snapshot(project_id, "worldbook_entry", entry_id, row, "创建条目")
    return row


def get_worldbook_entry_detail(project_id: str, entry_id: str) -> dict:
    project_or_404(project_id)
    row = ensure_worldbook_entry(project_id, entry_id)
    row["relations"] = db.all(
        """SELECT r.*, s.title source_title, t.title target_title
           FROM worldbook_relations r
           JOIN worldbook_entries s ON s.id = r.source_id
           JOIN worldbook_entries t ON t.id = r.target_id
           WHERE r.project_id = ? AND (r.source_id = ? OR r.target_id = ?)
           ORDER BY r.created_at DESC""",
        (project_id, entry_id, entry_id),
    )
    row["script_references"] = db.all(
        "SELECT * FROM script_references WHERE project_id = ? AND ref_type = 'worldbook' AND ref_id = ? ORDER BY created_at DESC",
        (project_id, entry_id),
    )
    return row


def update_worldbook_entry_payload(project_id: str, entry_id: str, data: dict) -> dict:
    project_or_404(project_id)
    current = ensure_worldbook_entry(project_id, entry_id)
    fields, params = [], []
    for key in ("title", "content", "visibility", "status", "creator", "ai_prompt"):
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data.get(key))
    if "category_id" in data:
        fields.append("category_id = ?")
        params.append(validate_category(project_id, data.get("category_id")))
    if "importance" in data:
        fields.append("importance = ?")
        params.append(int(data.get("importance") or 3))
    if "structured_data" in data:
        fields.append("structured_data = ?")
        params.append(to_json(data.get("structured_data")))
    if "tags" in data:
        fields.append("tags = ?")
        params.append(to_json_array(data.get("tags")))
    if "ai_metadata" in data:
        fields.append("ai_metadata = ?")
        params.append(to_json(data.get("ai_metadata")))
    if fields:
        version = int(current.get("version") or 1) + 1
        fields.extend(["version = ?", "updated_at = ?"])
        params.extend([version, now(), project_id, entry_id])
        db.exec(f"UPDATE worldbook_entries SET {', '.join(fields)} WHERE project_id = ? AND id = ?", tuple(params))
    updated = ensure_worldbook_entry(project_id, entry_id)
    create_version_snapshot(project_id, "worldbook_entry", entry_id, updated, ai_update_summary(data, "更新条目"))
    record_ai_apply_metadata(project_id, "worldbook", entry_id, data, updated)
    return updated


def delete_worldbook_entry_payload(project_id: str, entry_id: str) -> None:
    project_or_404(project_id)
    ensure_worldbook_entry(project_id, entry_id)
    db.exec("DELETE FROM script_references WHERE project_id = ? AND ref_type = 'worldbook' AND ref_id = ?", (project_id, entry_id))
    character_rows = db.all("SELECT id, world_entry_ids FROM characters WHERE project_id = ? AND world_entry_ids LIKE ?", (project_id, f"%{entry_id}%"))
    for row in character_rows:
        world_ids = parse_json(row.get("world_entry_ids"), [])
        if entry_id in world_ids:
            db.exec(
                "UPDATE characters SET world_entry_ids = ?, updated_at = ? WHERE project_id = ? AND id = ?",
                (to_json_array([item for item in world_ids if item != entry_id]), now(), project_id, row["id"]),
            )
    deleted = db.exec("DELETE FROM worldbook_entries WHERE project_id = ? AND id = ?", (project_id, entry_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="条目不存在")


def list_worldbook_relations(project_id: str) -> list[dict]:
    project_or_404(project_id)
    return db.all(
        """SELECT r.*, s.title source_title, t.title target_title
           FROM worldbook_relations r
           JOIN worldbook_entries s ON s.id = r.source_id
           JOIN worldbook_entries t ON t.id = r.target_id
           WHERE r.project_id = ?
           ORDER BY r.created_at DESC""",
        (project_id,),
    )


def create_worldbook_relation_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    source_id = data.get("source_id")
    target_id = data.get("target_id")
    if source_id == target_id:
        raise HTTPException(status_code=400, detail="不能关联自身")
    ensure_worldbook_entry(project_id, source_id)
    ensure_worldbook_entry(project_id, target_id)
    relation_id = new_id("wrel")
    db.exec(
        """INSERT INTO worldbook_relations (id, project_id, source_id, target_id, relation_type, label, strength, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            relation_id,
            project_id,
            source_id,
            target_id,
            data.get("relation_type", "related"),
            data.get("label", ""),
            int(data.get("strength") or 3),
            data.get("description", ""),
            now(),
        ),
    )
    return db.one("SELECT * FROM worldbook_relations WHERE id = ?", (relation_id,))


def delete_worldbook_relation_payload(project_id: str, relation_id: str) -> None:
    project_or_404(project_id)
    deleted = db.exec("DELETE FROM worldbook_relations WHERE project_id = ? AND id = ?", (project_id, relation_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="关联不存在")


def build_worldbook_graph(project_id: str, category_id: Optional[str] = None, min_importance: int = 1) -> dict:
    project_or_404(project_id)
    entries = list_worldbook_entries(project_id, category_id=category_id, min_importance=min_importance)
    ids = {entry["id"] for entry in entries}
    relations = [row for row in list_worldbook_relations(project_id) if row["source_id"] in ids and row["target_id"] in ids]
    nodes = [{"id": e["id"], "label": e["title"], "importance": e["importance"], "category_id": e["category_id"]} for e in entries]
    edges = [{"id": r["id"], "from": r["source_id"], "to": r["target_id"], "type": r["relation_type"], "label": r["label"], "strength": r["strength"]} for r in relations]
    return {"nodes": nodes, "edges": edges}


def export_worldbook(project_id: str, format: str = "markdown", ids: str = "") -> dict:
    project_or_404(project_id)
    selected = [item for item in ids.split(",") if item]
    rows = list_worldbook_entries(project_id)
    if selected:
        rows = [row for row in rows if row["id"] in selected]
    return export_worldbook_payload(rows, list_worldbook_categories(project_id), list_worldbook_relations(project_id), format)
