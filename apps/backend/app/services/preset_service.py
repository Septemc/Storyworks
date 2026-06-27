from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from ..database import compile_preset, db, new_id, now, parse_json, project_or_404, record_version, to_json_array
from .ai_service import clean_text, record_ai_operation


PRESET_JSON_FIELDS = {"dimensions": [], "custom_blocks": [], "application_scenes": [], "tags": []}


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


def get_preset(project_id: str, preset_id: str) -> dict | None:
    row = db.one("SELECT * FROM presets WHERE project_id = ? AND id = ?", (project_id, preset_id))
    return parse_row_fields(row, PRESET_JSON_FIELDS)


def ensure_preset(project_id: str, preset_id: str) -> dict:
    return require_row(get_preset(project_id, preset_id), "预设不存在")


def list_presets(project_id: str, category: str = "", q: str = "") -> list[dict]:
    project_or_404(project_id)
    sql = "SELECT * FROM presets WHERE project_id = ?"
    params: list[Any] = [project_id]
    if category:
        sql += " AND category = ?"
        params.append(category)
    if q:
        sql += " AND (name LIKE ? OR description LIKE ? OR dimensions LIKE ? OR custom_blocks LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])
    sql += " ORDER BY updated_at DESC"
    return [parse_row_fields(row, PRESET_JSON_FIELDS) for row in db.all(sql, tuple(params))]


def create_preset_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    name = clean_text(data.get("name"))
    if not name:
        raise HTTPException(status_code=400, detail="预设名称不能为空")
    dimensions = data.get("dimensions") or []
    blocks = data.get("custom_blocks") or []
    scenes = data.get("application_scenes") or []
    compiled = data.get("compiled_prompt") or compile_preset(dimensions, blocks, scenes)
    stamp = now()
    preset_id = new_id("preset")
    db.exec(
        """INSERT INTO presets
           (id, project_id, name, description, dimensions, custom_blocks, compiled_prompt, application_scenes, tags, category, ai_generated, generation_input, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            preset_id,
            project_id,
            name,
            data.get("description", ""),
            to_json_array(dimensions),
            to_json_array(blocks),
            compiled,
            to_json_array(scenes),
            to_json_array(data.get("tags")),
            data.get("category", "general"),
            1 if data.get("ai_generated") else 0,
            data.get("generation_input", ""),
            stamp,
            stamp,
        ),
    )
    row = ensure_preset(project_id, preset_id)
    record_version(project_id, "preset", preset_id, 1, row, "创建预设")
    return row


def update_preset_payload(project_id: str, preset_id: str, data: dict) -> dict:
    project_or_404(project_id)
    current = ensure_preset(project_id, preset_id)
    dimensions = data.get("dimensions", current["dimensions"])
    blocks = data.get("custom_blocks", current["custom_blocks"])
    scenes = data.get("application_scenes", current["application_scenes"])
    fields, params = [], []
    for key in ("name", "description", "category", "generation_input"):
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data.get(key))
    if "dimensions" in data:
        fields.append("dimensions = ?")
        params.append(to_json_array(dimensions))
    if "custom_blocks" in data:
        fields.append("custom_blocks = ?")
        params.append(to_json_array(blocks))
    if "application_scenes" in data:
        fields.append("application_scenes = ?")
        params.append(to_json_array(scenes))
    if "tags" in data:
        fields.append("tags = ?")
        params.append(to_json_array(data.get("tags")))
    if any(key in data for key in ("dimensions", "custom_blocks", "application_scenes")) or data.get("recompile"):
        fields.append("compiled_prompt = ?")
        params.append(compile_preset(dimensions, blocks, scenes))
    elif "compiled_prompt" in data:
        fields.append("compiled_prompt = ?")
        params.append(data.get("compiled_prompt"))
    if fields:
        fields.append("updated_at = ?")
        params.extend([now(), project_id, preset_id])
        db.exec(f"UPDATE presets SET {', '.join(fields)} WHERE project_id = ? AND id = ?", tuple(params))
    updated = ensure_preset(project_id, preset_id)
    if fields:
        record_version(project_id, "preset", preset_id, next_version_number(project_id, "preset", preset_id), updated, ai_update_summary(data, "更新预设"))
        record_ai_apply_metadata(project_id, "preset", preset_id, data, updated)
    return updated


def delete_preset_payload(project_id: str, preset_id: str) -> None:
    project_or_404(project_id)
    deleted = db.exec("DELETE FROM presets WHERE project_id = ? AND id = ?", (project_id, preset_id))
    if deleted <= 0:
        raise HTTPException(status_code=404, detail="预设不存在")


def apply_preset_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    preset_row = ensure_preset(project_id, data.get("preset_id"))
    scene_type = data.get("scene_type", "general")
    scene_requirements = data.get("scene_requirements", "")
    prompt = preset_row.get("compiled_prompt", "")
    scene = next((s for s in preset_row.get("application_scenes", []) if s.get("sceneType") == scene_type or s.get("scene_type") == scene_type), None)
    if scene and scene.get("adjustments"):
        prompt += f"\n\n[场景调整]\n{scene.get('adjustments')}"
    if scene_requirements:
        prompt += f"\n\n[本次任务要求]\n{scene_requirements}"
    return {"prompt": prompt}


def combine_presets_payload(project_id: str, data: dict) -> dict:
    project_or_404(project_id)
    base = require_row(get_preset(project_id, data.get("base_id")), "基础预设不存在")
    override = get_preset(project_id, data.get("override_id")) if data.get("override_id") else None
    dimensions = {d.get("name"): d for d in base.get("dimensions", [])}
    if override:
        for item in override.get("dimensions", []):
            dimensions[item.get("name")] = item
    blocks = base.get("custom_blocks", []) + (override.get("custom_blocks", []) if override else [])
    scenes = base.get("application_scenes", []) + (override.get("application_scenes", []) if override else [])
    return {
        "dimensions": list(dimensions.values()),
        "custom_blocks": blocks,
        "application_scenes": scenes,
        "compiled_prompt": compile_preset(list(dimensions.values()), blocks, scenes),
    }


def export_presets(project_id: str, format: str = "json") -> dict:
    rows = list_presets(project_id)
    if format == "markdown":
        lines = ["# 预设导出", ""]
        for row in rows:
            lines.extend([f"## {row['name']}", row.get("description", ""), "", "```", row.get("compiled_prompt", ""), "```", ""])
        return {"filename": "presets.md", "content": "\n".join(lines)}
    return {"filename": "presets.json", "content": json.dumps(rows, ensure_ascii=False, indent=2)}
