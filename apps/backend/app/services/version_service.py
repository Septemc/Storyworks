from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from ..database import db, parse_json, project_or_404
from .character_service import ensure_character, update_character_payload
from .preset_service import ensure_preset, update_preset_payload
from .script_service import ensure_script, update_script_payload
from .worldbook_service import ensure_worldbook_entry, update_worldbook_entry_payload


def flatten_for_diff(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_for_diff(child, path))
        return result
    return {prefix or "$": value}


def build_version_diff(snapshot: dict, current: dict) -> list[dict]:
    before = flatten_for_diff(snapshot)
    after = flatten_for_diff(current)
    rows: list[dict] = []
    for path in sorted(set(before) | set(after)):
        old_value = before.get(path)
        new_value = after.get(path)
        if old_value == new_value:
            continue
        if path not in before:
            change_type = "added"
        elif path not in after:
            change_type = "removed"
        else:
            change_type = "changed"
        rows.append({"path": path, "type": change_type, "before": old_value, "after": new_value})
    return rows


def current_version_entity(project_id: str, entity_type: str, entity_id: str) -> dict:
    if entity_type == "worldbook_entry":
        return ensure_worldbook_entry(project_id, entity_id)
    if entity_type == "character":
        return ensure_character(project_id, entity_id)
    if entity_type == "script":
        return ensure_script(project_id, entity_id)
    if entity_type == "preset":
        return ensure_preset(project_id, entity_id)
    raise HTTPException(status_code=400, detail="不支持的版本类型")


def list_versions(project_id: str, entity_type: str, entity_id: str) -> list[dict]:
    project_or_404(project_id)
    rows = db.all(
        "SELECT * FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ? ORDER BY version DESC, created_at DESC",
        (project_id, entity_type, entity_id),
    )
    for row in rows:
        row["data"] = parse_json(row.get("data"), {})
    return rows


def version_diff_payload(project_id: str, version_id: str) -> dict:
    project_or_404(project_id)
    row = db.one("SELECT * FROM version_history WHERE project_id = ? AND id = ?", (project_id, version_id))
    if row is None:
        raise HTTPException(status_code=404, detail="版本不存在")
    snapshot = parse_json(row["data"], {})
    current = current_version_entity(project_id, row["entity_type"], row["entity_id"])
    return {
        "version": {**row, "data": snapshot},
        "current": current,
        "diffs": build_version_diff(snapshot, current),
    }


def restore_version_payload(project_id: str, version_id: str) -> dict:
    project_or_404(project_id)
    row = db.one("SELECT * FROM version_history WHERE project_id = ? AND id = ?", (project_id, version_id))
    if row is None:
        raise HTTPException(status_code=404, detail="版本不存在")
    data = parse_json(row["data"], {})
    entity_type = row["entity_type"]
    restore_payload = {**data, "_version_summary": f"恢复版本 {row['version']}"}
    restored = None
    if entity_type == "worldbook_entry":
        restored = update_worldbook_entry_payload(project_id, row["entity_id"], restore_payload)
    elif entity_type == "character":
        restored = update_character_payload(project_id, row["entity_id"], restore_payload)
    elif entity_type == "script":
        restored = update_script_payload(project_id, row["entity_id"], restore_payload)
    elif entity_type == "preset":
        restored = update_preset_payload(project_id, row["entity_id"], restore_payload)
    else:
        raise HTTPException(status_code=400, detail="不支持的版本类型")
    return {
        "entity_type": entity_type,
        "entity_id": row["entity_id"],
        "restored_version": row["version"],
        "entity": restored,
    }
