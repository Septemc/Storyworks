from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from ..database import db, new_id, now, parse_json, project_or_404, record_version, to_json, to_json_array
from .ai_service import clean_text, record_ai_operation
from .character_schema import default_character_data, normalize_character_contract, apply_player_visibility
from .export_service import export_characters_payload
from .worldbook_service import get_worldbook_entry, ensure_worldbook_entry


CHARACTER_JSON_FIELDS = {
    "developer_data": {},
    "player_data": {},
    "field_visibility": {},
    "world_entry_ids": [],
    "tags": [],
    "generation_history": [],
}


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


def get_character(project_id: str, character_id: str) -> dict | None:
    row = db.one("SELECT * FROM characters WHERE project_id = ? AND id = ?", (project_id, character_id))
    return normalize_character_contract(parse_row_fields(row, CHARACTER_JSON_FIELDS))


def ensure_character(project_id: str, character_id: str) -> dict:
    return require_row(get_character(project_id, character_id), "角色不存在")


def list_characters(project_id: str, q: str = "", character_type: str = "", status: str = "", tag: str = "") -> list[dict]:
    project_or_404(project_id)
    sql = "SELECT * FROM characters WHERE project_id = ?"
    params: list[Any] = [project_id]
    if character_type:
        sql += " AND character_type = ?"
        params.append(character_type)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if q:
        sql += " AND (name LIKE ? OR developer_data LIKE ? OR tags LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if tag:
        sql += " AND tags LIKE ?"
        params.append(f"%{tag}%")
    sql += " ORDER BY updated_at DESC"
    return [normalize_character_contract(parse_row_fields(row, CHARACTER_JSON_FIELDS)) for row in db.all(sql, tuple(params))]


def normalize_character_input(name: str, data: dict) -> tuple[dict, dict, dict]:
    developer = data.get("developer_data")
    player = data.get("player_data")
    visibility = data.get("field_visibility")
    if not developer:
        developer, player, visibility = default_character_data(name, data.get("concept", ""))
    normalized = normalize_character_contract(
        {
            "developer_data": developer,
            "player_data": player or {},
            "field_visibility": visibility or {},
        }
    )
    developer = normalized["developer_data"]
    visibility = normalized["field_visibility"]
    player = normalized["player_data"] if player else apply_player_visibility(developer, visibility)
    return developer, player, visibility


def create_character_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    name = clean_text(data.get("name"))
    if not name:
        raise HTTPException(status_code=400, detail="角色名称不能为空")
    developer, player, visibility = normalize_character_input(name, data)
    stamp = now()
    character_id = new_id("char")
    world_ids = data.get("world_entry_ids") or []
    for entry_id in world_ids:
        ensure_worldbook_entry(project_id, entry_id)
    db.exec(
        """INSERT INTO characters
           (id, project_id, name, character_type, developer_data, player_data, field_visibility, world_entry_ids, tags, status, ai_generated, generation_history, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            character_id,
            project_id,
            name,
            data.get("character_type", "supporting"),
            to_json(developer),
            to_json(player),
            to_json(visibility or {}),
            to_json_array(world_ids),
            to_json_array(data.get("tags")),
            data.get("status", "active"),
            1 if data.get("ai_generated") else 0,
            to_json_array(data.get("generation_history")),
            stamp,
            stamp,
        ),
    )
    row = ensure_character(project_id, character_id)
    record_version(project_id, "character", character_id, 1, row, "创建角色")
    return row


def get_character_detail(project_id: str, character_id: str) -> dict:
    project_or_404(project_id)
    row = ensure_character(project_id, character_id)
    row["relations"] = db.all(
        """SELECT r.*, s.name source_name, t.name target_name
           FROM character_relations r
           JOIN characters s ON s.id = r.source_id
           JOIN characters t ON t.id = r.target_id
           WHERE r.project_id = ? AND (r.source_id = ? OR r.target_id = ?)
           ORDER BY r.updated_at DESC""",
        (project_id, character_id, character_id),
    )
    for rel in row["relations"]:
        rel["events"] = parse_json(rel.get("events"), [])
    row["world_entries"] = []
    for entry_id in row.get("world_entry_ids", []):
        entry = get_worldbook_entry(project_id, entry_id)
        if entry:
            row["world_entries"].append(entry)
    row["script_references"] = db.all(
        "SELECT * FROM script_references WHERE project_id = ? AND ref_type = 'character' AND ref_id = ? ORDER BY created_at DESC",
        (project_id, character_id),
    )
    return row


def update_character_payload(project_id: str, character_id: str, data: dict) -> dict:
    project_or_404(project_id)
    current = ensure_character(project_id, character_id)
    fields, params = [], []
    for key in ("name", "character_type", "status"):
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data.get(key))
    developer = data.get("developer_data", current["developer_data"])
    visibility = data.get("field_visibility", current["field_visibility"])
    normalized = normalize_character_contract(
        {
            "developer_data": developer,
            "player_data": data.get("player_data", current["player_data"]),
            "field_visibility": visibility,
        }
    )
    developer = normalized["developer_data"]
    visibility = normalized["field_visibility"]
    if "developer_data" in data:
        fields.append("developer_data = ?")
        params.append(to_json(developer))
    if "field_visibility" in data:
        fields.append("field_visibility = ?")
        params.append(to_json(visibility))
    if "player_data" in data:
        player = normalized["player_data"]
    elif "developer_data" in data or "field_visibility" in data:
        player = apply_player_visibility(developer, visibility)
    else:
        player = None
    if player is not None:
        fields.append("player_data = ?")
        params.append(to_json(player))
    if "world_entry_ids" in data:
        for entry_id in data.get("world_entry_ids") or []:
            ensure_worldbook_entry(project_id, entry_id)
        fields.append("world_entry_ids = ?")
        params.append(to_json_array(data.get("world_entry_ids")))
    if "tags" in data:
        fields.append("tags = ?")
        params.append(to_json_array(data.get("tags")))
    if "generation_history" in data:
        fields.append("generation_history = ?")
        params.append(to_json_array(data.get("generation_history")))
    if fields:
        fields.append("updated_at = ?")
        params.extend([now(), project_id, character_id])
        db.exec(f"UPDATE characters SET {', '.join(fields)} WHERE project_id = ? AND id = ?", tuple(params))
    updated = ensure_character(project_id, character_id)
    record_version(project_id, "character", character_id, next_version_number(project_id, "character", character_id), updated, ai_update_summary(data, "更新角色"))
    record_ai_apply_metadata(project_id, "character", character_id, data, updated)
    return updated


def delete_character_payload(project_id: str, character_id: str) -> None:
    project_or_404(project_id)
    ensure_character(project_id, character_id)
    db.exec("DELETE FROM script_references WHERE project_id = ? AND ref_type = 'character' AND ref_id = ?", (project_id, character_id))
    db.exec("DELETE FROM character_relations WHERE project_id = ? AND (source_id = ? OR target_id = ?)", (project_id, character_id, character_id))
    deleted = db.exec("DELETE FROM characters WHERE project_id = ? AND id = ?", (project_id, character_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="角色不存在")


def list_character_relations(project_id: str) -> list[dict]:
    project_or_404(project_id)
    rows = db.all(
        """SELECT r.*, s.name source_name, t.name target_name
           FROM character_relations r
           JOIN characters s ON s.id = r.source_id
           JOIN characters t ON t.id = r.target_id
           WHERE r.project_id = ?
           ORDER BY r.updated_at DESC""",
        (project_id,),
    )
    for row in rows:
        row["events"] = parse_json(row.get("events"), [])
    return rows


def create_character_relation_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    source_id, target_id = data.get("source_id"), data.get("target_id")
    if source_id == target_id:
        raise HTTPException(status_code=400, detail="不能关联自身")
    ensure_character(project_id, source_id)
    ensure_character(project_id, target_id)
    relation_id = new_id("crel")
    stamp = now()
    db.exec(
        """INSERT INTO character_relations
           (id, project_id, source_id, target_id, relation_type, direction, description, numeric_value, events, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            relation_id,
            project_id,
            source_id,
            target_id,
            data.get("relation_type", "friend"),
            data.get("direction", "bidirectional"),
            data.get("description", ""),
            int(data.get("numeric_value") or 0),
            to_json_array(data.get("events")),
            stamp,
            stamp,
        ),
    )
    return parse_row_fields(db.one("SELECT * FROM character_relations WHERE id = ?", (relation_id,)), {"events": []})


def delete_character_relation_payload(project_id: str, relation_id: str) -> None:
    project_or_404(project_id)
    deleted = db.exec("DELETE FROM character_relations WHERE project_id = ? AND id = ?", (project_id, relation_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="关系不存在")


def build_character_graph(project_id: str) -> dict:
    chars = list_characters(project_id)
    rels = list_character_relations(project_id)
    return {
        "nodes": [{"id": c["id"], "label": c["name"], "type": c["character_type"], "status": c["status"]} for c in chars],
        "edges": [{"id": r["id"], "from": r["source_id"], "to": r["target_id"], "type": r["relation_type"], "value": r["numeric_value"], "direction": r["direction"]} for r in rels],
    }


def export_characters(project_id: str, format: str = "markdown", ids: str = "") -> dict:
    project_or_404(project_id)
    selected = [item for item in ids.split(",") if item]
    rows = list_characters(project_id)
    if selected:
        rows = [row for row in rows if row["id"] in selected]
    return export_characters_payload(rows, format)
