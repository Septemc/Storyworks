from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from ..database import db, new_id, now, parse_json, project_or_404, record_version, to_json_array
from .ai_service import clean_text, record_ai_operation
from .tree_service import validate_parent_link


SCRIPT_JSON_FIELDS = {"tags": []}


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


def next_version_number(project_id: str, entity_type: str, entity_id: str) -> int:
    row = db.one(
        "SELECT COALESCE(MAX(version), 0) + 1 AS version FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ?",
        (project_id, entity_type, entity_id),
    )
    return int(row["version"] or 1)


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


def get_script(project_id: str, script_id: str) -> dict | None:
    row = db.one("SELECT * FROM scripts WHERE project_id = ? AND id = ?", (project_id, script_id))
    return parse_row_fields(row, SCRIPT_JSON_FIELDS)


def ensure_script(project_id: str, script_id: str) -> dict:
    return require_row(get_script(project_id, script_id), "剧本节点不存在")


def list_scripts(project_id: str, node_type: str = "", status: str = "", q: str = "") -> list[dict]:
    project_or_404(project_id)
    sql = "SELECT * FROM scripts WHERE project_id = ?"
    params: list[Any] = [project_id]
    if node_type:
        sql += " AND node_type = ?"
        params.append(node_type)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if q:
        sql += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    sql += " ORDER BY sort_order, created_at"
    return [parse_row_fields(row, SCRIPT_JSON_FIELDS) for row in db.all(sql, tuple(params))]


def build_script_tree(project_id: str) -> list[dict]:
    rows = list_scripts(project_id)
    by_parent: dict[str | None, list[dict]] = {}
    for row in rows:
        row["children"] = []
        by_parent.setdefault(row.get("parent_id"), []).append(row)

    def attach(node: dict) -> dict:
        node["children"] = by_parent.get(node["id"], [])
        for child in node["children"]:
            attach(child)
        return node

    return [attach(node) for node in by_parent.get(None, [])]


def create_script_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    title = clean_text(data.get("title"))
    if not title:
        raise HTTPException(status_code=400, detail="节点标题不能为空")
    parent_id = validate_parent_link(project_id, "scripts", "__new_script__", data.get("parent_id"))
    stamp = now()
    script_id = new_id("scr")
    db.exec(
        """INSERT INTO scripts
           (id, project_id, parent_id, node_type, title, content, summary, sort_order, status, tags, importance, story_time, story_location, ai_generated, ai_prompt, version, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (
            script_id,
            project_id,
            parent_id,
            data.get("node_type", "outline"),
            title,
            data.get("content", ""),
            data.get("summary", ""),
            int(data.get("sort_order") or 0),
            data.get("status", "draft"),
            to_json_array(data.get("tags")),
            int(data.get("importance") or 3),
            data.get("story_time", ""),
            data.get("story_location", ""),
            1 if data.get("ai_generated") else 0,
            data.get("ai_prompt", ""),
            stamp,
            stamp,
        ),
    )
    row = ensure_script(project_id, script_id)
    create_version_snapshot(project_id, "script", script_id, row, "创建剧本节点")
    return row


def get_script_detail(project_id: str, script_id: str) -> dict:
    project_or_404(project_id)
    row = ensure_script(project_id, script_id)
    row["references"] = db.all("SELECT * FROM script_references WHERE project_id = ? AND script_id = ? ORDER BY created_at DESC", (project_id, script_id))
    return row


def update_script_payload(project_id: str, script_id: str, data: dict) -> dict:
    project_or_404(project_id)
    current = ensure_script(project_id, script_id)
    fields, params = [], []
    for key in ("parent_id", "node_type", "title", "content", "summary", "sort_order", "status", "importance", "story_time", "story_location", "ai_prompt"):
        if key in data:
            fields.append(f"{key} = ?")
            params.append(validate_parent_link(project_id, "scripts", script_id, data.get(key)) if key == "parent_id" else data.get(key))
    if "tags" in data:
        fields.append("tags = ?")
        params.append(to_json_array(data.get("tags")))
    if fields:
        version = int(current.get("version") or 1) + 1
        fields.extend(["version = ?", "updated_at = ?"])
        params.extend([version, now(), project_id, script_id])
        db.exec(f"UPDATE scripts SET {', '.join(fields)} WHERE project_id = ? AND id = ?", tuple(params))
    updated = ensure_script(project_id, script_id)
    create_version_snapshot(project_id, "script", script_id, updated, ai_update_summary(data, "更新剧本节点"))
    record_ai_apply_metadata(project_id, "script", script_id, data, updated)
    return updated


def script_descendant_ids(project_id: str, root_id: str) -> list[str]:
    rows = db.all("SELECT id, parent_id FROM scripts WHERE project_id = ?", (project_id,))
    children: dict[str | None, list[str]] = {}
    for row in rows:
        children.setdefault(row.get("parent_id"), []).append(row["id"])
    ordered: list[str] = []

    def walk(script_id: str) -> None:
        ordered.append(script_id)
        for child_id in children.get(script_id, []):
            walk(child_id)

    walk(root_id)
    return ordered


def delete_script_payload(project_id: str, script_id: str) -> dict:
    project_or_404(project_id)
    ensure_script(project_id, script_id)
    ids = script_descendant_ids(project_id, script_id)
    placeholders = ",".join("?" for _ in ids)
    db.exec(f"DELETE FROM script_references WHERE project_id = ? AND script_id IN ({placeholders})", tuple([project_id, *ids]))
    deleted = db.exec(f"DELETE FROM scripts WHERE project_id = ? AND id IN ({placeholders})", tuple([project_id, *ids]))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="剧本节点不存在")
    return {"deleted_ids": ids, "deleted_count": deleted}


def resolve_reference_target(project_id: str, ref_type: str, ref_id: str) -> str:
    if ref_type == "worldbook":
        row = db.one("SELECT title FROM worldbook_entries WHERE project_id = ? AND id = ?", (project_id, ref_id))
        return require_row(row, "世界书条目不存在")["title"]
    if ref_type == "character":
        row = db.one("SELECT name FROM characters WHERE project_id = ? AND id = ?", (project_id, ref_id))
        return require_row(row, "角色不存在")["name"]
    raise HTTPException(status_code=400, detail="引用类型必须是 worldbook 或 character")


def add_script_reference_payload(project_id: str, script_id: str, data: dict) -> dict:
    project_or_404(project_id)
    ensure_script(project_id, script_id)
    ref_type = data.get("ref_type")
    ref_id = data.get("ref_id")
    ref_name = resolve_reference_target(project_id, ref_type, ref_id)
    ref_row_id = new_id("ref")
    db.exec(
        """INSERT INTO script_references (id, project_id, script_id, ref_type, ref_id, ref_name, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (ref_row_id, project_id, script_id, ref_type, ref_id, ref_name, data.get("description", ""), now()),
    )
    return db.one("SELECT * FROM script_references WHERE id = ?", (ref_row_id,))


def delete_script_reference_payload(project_id: str, reference_id: str) -> None:
    project_or_404(project_id)
    deleted = db.exec("DELETE FROM script_references WHERE project_id = ? AND id = ?", (project_id, reference_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="引用不存在")


def referenced_by(project_id: str, ref_type: str, ref_id: str) -> list[dict]:
    project_or_404(project_id)
    return db.all(
        """SELECT sr.*, s.title script_title, s.node_type
           FROM script_references sr
           JOIN scripts s ON s.id = sr.script_id
           WHERE sr.project_id = ? AND sr.ref_type = ? AND sr.ref_id = ?
           ORDER BY sr.created_at DESC""",
        (project_id, ref_type, ref_id),
    )


def export_scripts(project_id: str, format: str = "markdown") -> dict:
    project_or_404(project_id)
    tree = build_script_tree(project_id)
    if format == "json":
        return {"filename": "scripts.json", "content": json.dumps(tree, ensure_ascii=False, indent=2)}

    lines: list[str] = ["# 剧本导出", ""]

    def walk(nodes: list[dict], depth: int = 2) -> None:
        for node in nodes:
            lines.append(f"{'#' * depth} {node['title']}")
            if node.get("summary"):
                lines.extend(["", node["summary"]])
            if node.get("content"):
                lines.extend(["", node["content"]])
            lines.append("")
            walk(node.get("children", []), min(depth + 1, 6))

    walk(tree)
    return {"filename": "scripts.md", "content": "\n".join(lines)}
