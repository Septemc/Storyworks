from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import HTTPException

from ..database import db, new_id, now, parse_json, project_or_404, to_json, to_json_array
from .character_schema import normalize_character_contract
from .ai_service import clean_text
from .export_service import export_project_payload


DEMO_PROJECT_IDS = {"proj_demo", "proj_demo_urban", "proj_demo_scifi"}
PROJECT_STATUSES = {"active", "archived"}
AI_DRAFT_TARGETS = {"worldbook", "character", "script", "preset"}
LEGACY_PREVIEW_LIMIT = 1600
PROJECT_WORLD_VISIBILITIES = {"public", "private", "secret"}
PROJECT_CHARACTER_VIEW_MODES = {"developer", "player"}
DEFAULT_PROJECT_SETTINGS = {
    "status": "active",
    "default_style": "",
    "ai": {"temperature": 0.7, "max_tokens": 4096},
    "modules": {"worldbook": True, "characters": True, "scripts": True, "presets": True},
    "defaults": {"worldbook_visibility": "public", "character_view_mode": "developer"},
}


def project_counts(project_id: str) -> dict:
    return {
        "worldbook": db.one("SELECT COUNT(*) c FROM worldbook_entries WHERE project_id = ?", (project_id,))["c"],
        "characters": db.one("SELECT COUNT(*) c FROM characters WHERE project_id = ?", (project_id,))["c"],
        "scripts": db.one("SELECT COUNT(*) c FROM scripts WHERE project_id = ?", (project_id,))["c"],
        "presets": db.one("SELECT COUNT(*) c FROM presets WHERE project_id = ?", (project_id,))["c"],
        "ai_drafts": pending_ai_draft_summary(project_id)["total"],
    }


def pending_ai_draft_summary(project_id: str, limit: int = 5) -> dict:
    logs = db.all(
        """SELECT id, target_type, target_id, operation, status, section, field, instruction, prompt, request, response_preview, response_data, created_at
           FROM ai_operation_logs
           WHERE project_id = ? AND operation IN ('iterate', 'apply')
           ORDER BY created_at DESC""",
        (project_id,),
    )
    apply_logs = [row for row in logs if row.get("operation") == "apply"]
    drafts = []
    by_target_type = {target: 0 for target in sorted(AI_DRAFT_TARGETS)}
    for row in logs:
        if not is_pending_ai_draft_candidate(row):
            continue
        if has_matching_apply_log(row, apply_logs):
            continue
        drafts.append(
            {
                "id": row["id"],
                "target_type": row["target_type"],
                "target_id": row.get("target_id") or "",
                "section": row.get("section") or "",
                "field": row.get("field") or "",
                "instruction": row.get("instruction") or "",
                "created_at": row.get("created_at") or "",
            }
        )
        by_target_type[row["target_type"]] = by_target_type.get(row["target_type"], 0) + 1
    return {"total": len(drafts), "by_target_type": by_target_type, "recent": drafts[:limit]}


def is_pending_ai_draft_candidate(row: dict) -> bool:
    if row.get("status") != "success" or row.get("operation") != "iterate":
        return False
    if row.get("target_type") not in AI_DRAFT_TARGETS or not row.get("target_id"):
        return False
    request = parse_json(row.get("request"), {})
    if request.get("apply") is True:
        return False
    response_data = parse_json(row.get("response_data"), None)
    preview = str(row.get("response_preview") or "")
    return response_data is not None or (bool(preview.strip()) and len(preview) < LEGACY_PREVIEW_LIMIT)


def has_matching_apply_log(draft: dict, apply_logs: list[dict]) -> bool:
    for log in apply_logs:
        if log.get("target_type") != draft.get("target_type") or log.get("target_id") != draft.get("target_id"):
            continue
        if (log.get("section") or "") != (draft.get("section") or "") or (log.get("field") or "") != (draft.get("field") or ""):
            continue
        if (log.get("prompt") or "") != (draft.get("prompt") or ""):
            continue
        if (log.get("created_at") or "") >= (draft.get("created_at") or ""):
            return True
    return False


def normalize_project_settings(value: Any) -> dict:
    raw = value if isinstance(value, dict) else {}
    settings = deepcopy(DEFAULT_PROJECT_SETTINGS)
    for key, item in raw.items():
        if key not in settings:
            settings[key] = item

    status = clean_text(raw.get("status") or settings["status"])
    settings["status"] = status if status in PROJECT_STATUSES else "active"
    settings["default_style"] = clean_text(raw.get("default_style") or raw.get("defaultStyle") or "")

    raw_ai = raw.get("ai") if isinstance(raw.get("ai"), dict) else {}
    ai = {key: item for key, item in raw_ai.items() if key not in settings["ai"]}
    ai["temperature"] = clamp_float(raw_ai.get("temperature"), 0.7, 0, 1.4)
    ai["max_tokens"] = clamp_int(raw_ai.get("max_tokens") or raw_ai.get("maxTokens"), 4096, 1024, 20000)
    settings["ai"] = ai

    raw_modules = raw.get("modules") if isinstance(raw.get("modules"), dict) else {}
    modules = {key: bool(raw_modules.get(key, default)) for key, default in DEFAULT_PROJECT_SETTINGS["modules"].items()}
    settings["modules"] = modules

    raw_defaults = raw.get("defaults") if isinstance(raw.get("defaults"), dict) else {}
    defaults = {key: item for key, item in raw_defaults.items() if key not in settings["defaults"]}
    visibility = clean_text(raw_defaults.get("worldbook_visibility") or raw_defaults.get("worldbookVisibility") or "public")
    view_mode = clean_text(raw_defaults.get("character_view_mode") or raw_defaults.get("characterViewMode") or "developer")
    defaults["worldbook_visibility"] = visibility if visibility in PROJECT_WORLD_VISIBILITIES else "public"
    defaults["character_view_mode"] = view_mode if view_mode in PROJECT_CHARACTER_VIEW_MODES else "developer"
    settings["defaults"] = defaults
    return settings


def merge_project_settings(current: Any, incoming: Any) -> dict:
    merged = normalize_project_settings(current)
    if not isinstance(incoming, dict):
        return merged
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return normalize_project_settings(merged)


def clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def serialize_project(row: dict, *, include_counts: bool = True) -> dict:
    payload = dict(row)
    settings = normalize_project_settings(parse_json(payload.get("settings"), {}))
    status = settings["status"]
    payload["settings"] = settings
    payload["status"] = status
    payload["is_demo"] = payload["id"] in DEMO_PROJECT_IDS
    if include_counts:
        payload["counts"] = project_counts(payload["id"])
    return payload


def parse_row_fields(row: dict | None, fields: dict[str, Any]) -> dict | None:
    if not row:
        return None
    for key, default in fields.items():
        row[key] = parse_json(row.get(key), default)
    return row


def list_projects(include_archived: bool = False) -> list[dict]:
    rows = db.all("SELECT * FROM projects ORDER BY updated_at DESC")
    projects_payload = [serialize_project(row) for row in rows]
    if not include_archived:
        projects_payload = [row for row in projects_payload if row["status"] != "archived"]
    return projects_payload


def create_project_payload(data: dict) -> dict:
    name = clean_text(data.get("name"))
    if not name:
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    if db.one("SELECT id FROM projects WHERE name = ?", (name,)):
        raise HTTPException(status_code=409, detail="项目名称已存在")
    stamp = now()
    project_id = new_id("proj")
    db.exec(
        "INSERT INTO projects (id, name, description, genre, settings, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            project_id,
            name,
            data.get("description", ""),
            data.get("genre", ""),
            to_json(normalize_project_settings({**(data.get("settings") or {}), "status": "active"})),
            stamp,
            stamp,
        ),
    )
    for order, item in enumerate(data.get("categories") or []):
        db.exec(
            """INSERT INTO worldbook_categories (id, project_id, parent_id, name, description, template, custom_fields, sort_order, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_id("cat"),
                project_id,
                item.get("parent_id"),
                item.get("name", "未命名分类"),
                item.get("description", ""),
                to_json(item.get("template") or {"sections": []}),
                to_json_array(item.get("custom_fields")),
                order,
                stamp,
                stamp,
            ),
        )
    if not data.get("categories"):
        for order, name_cn in enumerate(["历史", "地理", "政治", "人文", "阵营", "体系"]):
            db.exec(
                """INSERT INTO worldbook_categories (id, project_id, parent_id, name, description, template, custom_fields, sort_order, created_at, updated_at)
                   VALUES (?, ?, NULL, ?, '', ?, '[]', ?, ?, ?)""",
                (new_id("cat"), project_id, name_cn, to_json({"sections": []}), order, stamp, stamp),
            )
    return serialize_project(db.one("SELECT * FROM projects WHERE id = ?", (project_id,)))


def update_project_payload(project_id: str, data: dict) -> dict:
    current = project_or_404(project_id)
    fields = []
    params = []
    for key in ("name", "description", "genre"):
        if key in data:
            if key == "name":
                name = clean_text(data.get("name"))
                if not name:
                    raise HTTPException(status_code=400, detail="项目名称不能为空")
                existing = db.one("SELECT id FROM projects WHERE name = ? AND id != ?", (name, project_id))
                if existing:
                    raise HTTPException(status_code=409, detail="项目名称已存在")
                fields.append("name = ?")
                params.append(name)
                continue
            fields.append(f"{key} = ?")
            params.append(data.get(key))
    settings = normalize_project_settings(parse_json(current.get("settings"), {}))
    if "settings" in data:
        settings = merge_project_settings(settings, data.get("settings") or {})
    if "status" in data:
        status = clean_text(data.get("status") or "active")
        if status not in PROJECT_STATUSES:
            raise HTTPException(status_code=400, detail="不支持的项目状态")
        settings["status"] = status
        settings = normalize_project_settings(settings)
    if "settings" in data or "status" in data:
        fields.append("settings = ?")
        params.append(to_json(settings))
    if fields:
        fields.append("updated_at = ?")
        params.append(now())
        params.append(project_id)
        db.exec(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", tuple(params))
    return serialize_project(project_or_404(project_id))


def update_project_status(project_id: str, status: str) -> dict:
    if status not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail="不支持的项目状态")
    row = project_or_404(project_id)
    settings = normalize_project_settings(parse_json(row.get("settings"), {}))
    settings["status"] = status
    db.exec("UPDATE projects SET settings = ?, updated_at = ? WHERE id = ?", (to_json(settings), now(), project_id))
    return serialize_project(project_or_404(project_id))


def reset_demo_project_payload(project_id: str) -> dict:
    if project_id not in DEMO_PROJECT_IDS:
        raise HTTPException(status_code=400, detail="只有内置 demo 项目可以重置")
    from ..database import seed_project
    from ..demo_data import seed_demo_content

    project_or_404(project_id)
    db.exec("DELETE FROM projects WHERE id = ?", (project_id,))
    seed_project()
    seed_demo_content()
    return serialize_project(project_or_404(project_id))


def delete_project_payload(project_id: str, confirm_name: str) -> None:
    project = project_or_404(project_id)
    if project_id in DEMO_PROJECT_IDS:
        raise HTTPException(status_code=400, detail="内置 demo 项目不能删除，请使用 demo 重置")
    if clean_text(confirm_name) != project["name"]:
        raise HTTPException(status_code=400, detail="请输入完整项目名称确认删除")
    db.exec("DELETE FROM projects WHERE id = ?", (project_id,))


def project_overview(project_id: str) -> dict:
    project_or_404(project_id)
    return {
        "pending_ai_drafts": pending_ai_draft_summary(project_id),
        "recent": {
            "worldbook": db.all("SELECT id, title, updated_at FROM worldbook_entries WHERE project_id = ? ORDER BY updated_at DESC LIMIT 5", (project_id,)),
            "characters": db.all("SELECT id, name title, updated_at FROM characters WHERE project_id = ? ORDER BY updated_at DESC LIMIT 5", (project_id,)),
            "scripts": db.all("SELECT id, title, updated_at FROM scripts WHERE project_id = ? ORDER BY updated_at DESC LIMIT 5", (project_id,)),
            "presets": db.all("SELECT id, name title, updated_at FROM presets WHERE project_id = ? ORDER BY updated_at DESC LIMIT 5", (project_id,)),
        }
    }


def project_ai_logs(project_id: str, target_type: str = "", target_id: str = "", limit: int | None = 50) -> list[dict]:
    project_or_404(project_id)
    sql = "SELECT * FROM ai_operation_logs WHERE project_id = ?"
    params: list[Any] = [project_id]
    if target_type:
        sql += " AND target_type = ?"
        params.append(target_type)
    if target_id:
        sql += " AND target_id = ?"
        params.append(target_id)
    sql += " ORDER BY created_at DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    rows = db.all(sql, tuple(params))
    apply_logs = db.all(
        """SELECT target_type, target_id, section, field, prompt, created_at
           FROM ai_operation_logs
           WHERE project_id = ? AND operation = 'apply'""",
        (project_id,),
    )
    for row in rows:
        candidate = is_pending_ai_draft_candidate(row)
        applied_preview = candidate and has_matching_apply_log(row, apply_logs)
        row["pending_apply"] = bool(candidate and not applied_preview)
        row["applied_preview"] = bool(applied_preview)
        row["request"] = parse_json(row.get("request"), {})
        row["response_data"] = parse_json(row.get("response_data"), parse_json(row.get("response_preview"), None))
        row["process_log"] = parse_json(row.get("process_log"), [])
    return rows


def project_worldbook_categories(project_id: str) -> list[dict]:
    rows = db.all(
        "SELECT * FROM worldbook_categories WHERE project_id = ? ORDER BY parent_id IS NOT NULL, sort_order, name",
        (project_id,),
    )
    return [parse_row_fields(row, {"template": {"sections": []}, "custom_fields": []}) for row in rows]


def project_worldbook_entries(project_id: str) -> list[dict]:
    rows = db.all(
        "SELECT * FROM worldbook_entries WHERE project_id = ? AND importance >= ? ORDER BY updated_at DESC",
        (project_id, 1),
    )
    return [parse_row_fields(row, {"structured_data": {}, "tags": [], "ai_metadata": {}}) for row in rows]


def project_worldbook_relations(project_id: str) -> list[dict]:
    return db.all(
        """SELECT r.*, s.title source_title, t.title target_title
           FROM worldbook_relations r
           JOIN worldbook_entries s ON s.id = r.source_id
           JOIN worldbook_entries t ON t.id = r.target_id
           WHERE r.project_id = ?
           ORDER BY r.created_at DESC""",
        (project_id,),
    )


def project_characters(project_id: str) -> list[dict]:
    rows = db.all("SELECT * FROM characters WHERE project_id = ? ORDER BY updated_at DESC", (project_id,))
    return [
        normalize_character_contract(
            parse_row_fields(row, {"developer_data": {}, "player_data": {}, "field_visibility": {}, "world_entry_ids": [], "tags": [], "generation_history": []})
        )
        for row in rows
    ]


def project_character_relations(project_id: str) -> list[dict]:
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


def project_scripts(project_id: str) -> list[dict]:
    rows = db.all("SELECT * FROM scripts WHERE project_id = ? ORDER BY sort_order, created_at", (project_id,))
    return [parse_row_fields(row, {"tags": []}) for row in rows]


def project_script_tree(project_id: str) -> list[dict]:
    nodes = project_scripts(project_id)
    by_parent: dict[str | None, list[dict]] = {}
    for node in nodes:
        node["children"] = []
        by_parent.setdefault(node.get("parent_id"), []).append(node)

    def attach(node: dict):
        node["children"] = by_parent.get(node["id"], [])
        for child in node["children"]:
            attach(child)
        return node

    return [attach(node) for node in by_parent.get(None, [])]


def project_presets(project_id: str) -> list[dict]:
    rows = db.all("SELECT * FROM presets WHERE project_id = ? ORDER BY updated_at DESC", (project_id,))
    return [parse_row_fields(row, {"dimensions": [], "custom_blocks": [], "application_scenes": [], "tags": []}) for row in rows]


def project_versions(project_id: str) -> list[dict]:
    rows = db.all("SELECT * FROM version_history WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    for row in rows:
        row["data"] = parse_json(row.get("data"), {})
    return rows


def project_script_references(project_id: str) -> list[dict]:
    return db.all("SELECT * FROM script_references WHERE project_id = ? ORDER BY created_at DESC", (project_id,))


def build_project_export(project_id: str) -> dict:
    project = project_or_404(project_id)
    project["settings"] = parse_json(project.get("settings"), {})
    payload = {
        "worldbook": {
            "categories": project_worldbook_categories(project_id),
            "entries": project_worldbook_entries(project_id),
            "relations": project_worldbook_relations(project_id),
        },
        "characters": {
            "entries": project_characters(project_id),
            "relations": project_character_relations(project_id),
        },
        "scripts": {
            "entries": project_scripts(project_id),
            "tree": project_script_tree(project_id),
            "references": project_script_references(project_id),
        },
        "presets": project_presets(project_id),
        "versions": project_versions(project_id),
        "ai_operation_logs": project_ai_logs(project_id, limit=None),
    }
    return export_project_payload(project, payload)
