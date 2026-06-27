from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from ..database import db, new_id, now, parse_json, to_json, to_json_array


def _package_from_request(data: dict) -> dict:
    if "content" in data:
        try:
            package = json.loads(data.get("content") or "{}")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="导入内容不是有效 JSON") from exc
    elif "package" in data:
        package = data.get("package") or {}
    else:
        package = data
    if not isinstance(package, dict):
        raise HTTPException(status_code=400, detail="导入包格式不正确")
    return package


def validate_project_package(data: dict) -> dict:
    package = _package_from_request(data)
    issues: list[dict] = []
    if package.get("format_version") != 1:
        issues.append({"type": "format_version", "message": "仅支持 format_version = 1 的 Storyworks 导出包"})
    project = package.get("project") or {}
    if not project.get("name"):
        issues.append({"type": "project", "message": "导入包缺少项目名称"})

    worldbook = package.get("worldbook") or {}
    characters = package.get("characters") or {}
    scripts = package.get("scripts") or {}
    counts = {
        "worldbook_categories": len(worldbook.get("categories") or []),
        "worldbook_entries": len(worldbook.get("entries") or []),
        "worldbook_relations": len(worldbook.get("relations") or []),
        "characters": len(characters.get("entries") or []),
        "character_relations": len(characters.get("relations") or []),
        "scripts": len(scripts.get("entries") or []),
        "script_references": len(scripts.get("references") or []),
        "presets": len(package.get("presets") or []),
        "versions": len(package.get("versions") or []),
        "ai_operation_logs": len(package.get("ai_operation_logs") or []),
    }
    if not any(counts.values()):
        issues.append({"type": "content", "message": "导入包没有可导入的数据"})

    existing_name = bool(project.get("name") and db.one("SELECT id FROM projects WHERE name = ?", (project.get("name"),)))
    return {
        "valid": not issues,
        "format_version": package.get("format_version"),
        "project_name": project.get("name", ""),
        "name_available": not existing_name,
        "counts": counts,
        "issues": issues,
    }


def _unique_project_name(base_name: str) -> str:
    base = f"{base_name or '导入项目'}（导入）"
    if not db.one("SELECT id FROM projects WHERE name = ?", (base,)):
        return base
    index = 2
    while True:
        candidate = f"{base}-{index}"
        if not db.one("SELECT id FROM projects WHERE name = ?", (candidate,)):
            return candidate
        index += 1


def _map_id(source_id: str | None, mapping: dict[str, str]) -> str | None:
    if not source_id:
        return None
    return mapping.get(source_id)


def _rewrite_snapshot(entity_type: str, value: Any, new_project_id: str, id_maps: dict[str, dict[str, str]]) -> Any:
    if not isinstance(value, dict):
        return value
    data = dict(value)
    data["project_id"] = new_project_id
    if entity_type == "worldbook_entry":
        data["id"] = _map_id(data.get("id"), id_maps["worldbook_entries"]) or data.get("id")
        data["category_id"] = _map_id(data.get("category_id"), id_maps["worldbook_categories"])
    elif entity_type == "character":
        data["id"] = _map_id(data.get("id"), id_maps["characters"]) or data.get("id")
        data["world_entry_ids"] = [_map_id(item, id_maps["worldbook_entries"]) for item in parse_json(data.get("world_entry_ids"), []) if _map_id(item, id_maps["worldbook_entries"])]
    elif entity_type == "script":
        data["id"] = _map_id(data.get("id"), id_maps["scripts"]) or data.get("id")
        data["parent_id"] = _map_id(data.get("parent_id"), id_maps["scripts"])
    elif entity_type == "preset":
        data["id"] = _map_id(data.get("id"), id_maps["presets"]) or data.get("id")
    return data


def import_project_package(data: dict) -> dict:
    preview = validate_project_package(data)
    if not preview["valid"]:
        raise HTTPException(status_code=400, detail="导入包校验失败")

    package = _package_from_request(data)
    project = package.get("project") or {}
    stamp = now()
    new_project_id = new_id("proj")
    new_project_name = data.get("name") or _unique_project_name(project.get("name", "导入项目"))
    if db.one("SELECT id FROM projects WHERE name = ?", (new_project_name,)):
        raise HTTPException(status_code=409, detail="项目名称已存在")

    worldbook = package.get("worldbook") or {}
    characters = package.get("characters") or {}
    scripts = package.get("scripts") or {}
    presets = package.get("presets") or []
    versions = package.get("versions") or []
    ai_logs = package.get("ai_operation_logs") or []
    id_maps = {
        "worldbook_categories": {row["id"]: new_id("cat") for row in worldbook.get("categories") or []},
        "worldbook_entries": {row["id"]: new_id("world") for row in worldbook.get("entries") or []},
        "characters": {row["id"]: new_id("char") for row in characters.get("entries") or []},
        "scripts": {row["id"]: new_id("scr") for row in scripts.get("entries") or []},
        "presets": {row["id"]: new_id("preset") for row in presets},
    }
    version_id_map = {row["id"]: new_id("ver") for row in versions}
    log_id_map = {row["id"]: new_id("ailog") for row in ai_logs}

    with db.connect() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, description, genre, settings, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                new_project_id,
                new_project_name,
                project.get("description", ""),
                project.get("genre", ""),
                to_json(project.get("settings") or {}),
                stamp,
                stamp,
            ),
        )

        for row in worldbook.get("categories") or []:
            conn.execute(
                """INSERT INTO worldbook_categories
                   (id, project_id, parent_id, name, description, template, custom_fields, sort_order, created_at, updated_at)
                   VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_maps["worldbook_categories"][row["id"]],
                    new_project_id,
                    row.get("name", "未命名分类"),
                    row.get("description", ""),
                    to_json(row.get("template") or {"sections": []}),
                    to_json_array(row.get("custom_fields")),
                    int(row.get("sort_order") or 0),
                    stamp,
                    stamp,
                ),
            )
        for row in worldbook.get("categories") or []:
            parent_id = _map_id(row.get("parent_id"), id_maps["worldbook_categories"])
            conn.execute(
                "UPDATE worldbook_categories SET parent_id = ? WHERE project_id = ? AND id = ?",
                (parent_id, new_project_id, id_maps["worldbook_categories"][row["id"]]),
            )

        for row in worldbook.get("entries") or []:
            conn.execute(
                """INSERT INTO worldbook_entries
                   (id, project_id, category_id, title, content, structured_data, importance, visibility, status, tags, creator, ai_generated, ai_prompt, ai_metadata, version, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_maps["worldbook_entries"][row["id"]],
                    new_project_id,
                    _map_id(row.get("category_id"), id_maps["worldbook_categories"]),
                    row.get("title", "未命名条目"),
                    row.get("content", ""),
                    to_json(row.get("structured_data") or {}),
                    int(row.get("importance") or 3),
                    row.get("visibility", "public"),
                    row.get("status", "draft"),
                    to_json_array(row.get("tags")),
                    row.get("creator", ""),
                    1 if row.get("ai_generated") else 0,
                    row.get("ai_prompt", ""),
                    to_json(row.get("ai_metadata") or {}),
                    int(row.get("version") or 1),
                    stamp,
                    stamp,
                ),
            )
        for row in worldbook.get("relations") or []:
            source_id = _map_id(row.get("source_id"), id_maps["worldbook_entries"])
            target_id = _map_id(row.get("target_id"), id_maps["worldbook_entries"])
            if not source_id or not target_id or source_id == target_id:
                continue
            conn.execute(
                """INSERT INTO worldbook_relations (id, project_id, source_id, target_id, relation_type, label, strength, description, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (new_id("wrel"), new_project_id, source_id, target_id, row.get("relation_type", "related"), row.get("label", ""), int(row.get("strength") or 3), row.get("description", ""), stamp),
            )

        for row in characters.get("entries") or []:
            world_ids = [_map_id(item, id_maps["worldbook_entries"]) for item in row.get("world_entry_ids", [])]
            conn.execute(
                """INSERT INTO characters
                   (id, project_id, name, character_type, developer_data, player_data, field_visibility, world_entry_ids, tags, status, ai_generated, generation_history, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_maps["characters"][row["id"]],
                    new_project_id,
                    row.get("name", "未命名角色"),
                    row.get("character_type", "supporting"),
                    to_json(row.get("developer_data") or {}),
                    to_json(row.get("player_data") or {}),
                    to_json(row.get("field_visibility") or {}),
                    to_json_array([item for item in world_ids if item]),
                    to_json_array(row.get("tags")),
                    row.get("status", "active"),
                    1 if row.get("ai_generated") else 0,
                    to_json_array(row.get("generation_history")),
                    stamp,
                    stamp,
                ),
            )
        for row in characters.get("relations") or []:
            source_id = _map_id(row.get("source_id"), id_maps["characters"])
            target_id = _map_id(row.get("target_id"), id_maps["characters"])
            if not source_id or not target_id or source_id == target_id:
                continue
            conn.execute(
                """INSERT INTO character_relations
                   (id, project_id, source_id, target_id, relation_type, direction, description, numeric_value, events, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("crel"),
                    new_project_id,
                    source_id,
                    target_id,
                    row.get("relation_type", "friend"),
                    row.get("direction", "bidirectional"),
                    row.get("description", ""),
                    int(row.get("numeric_value") or 0),
                    to_json_array(row.get("events")),
                    stamp,
                    stamp,
                ),
            )

        for row in scripts.get("entries") or []:
            conn.execute(
                """INSERT INTO scripts
                   (id, project_id, parent_id, node_type, title, content, summary, sort_order, status, tags, importance, story_time, story_location, ai_generated, ai_prompt, version, created_at, updated_at)
                   VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_maps["scripts"][row["id"]],
                    new_project_id,
                    row.get("node_type", "scene"),
                    row.get("title", "未命名节点"),
                    row.get("content", ""),
                    row.get("summary", ""),
                    int(row.get("sort_order") or 0),
                    row.get("status", "draft"),
                    to_json_array(row.get("tags")),
                    int(row.get("importance") or 3),
                    row.get("story_time", ""),
                    row.get("story_location", ""),
                    1 if row.get("ai_generated") else 0,
                    row.get("ai_prompt", ""),
                    int(row.get("version") or 1),
                    stamp,
                    stamp,
                ),
            )
        for row in scripts.get("entries") or []:
            parent_id = _map_id(row.get("parent_id"), id_maps["scripts"])
            conn.execute("UPDATE scripts SET parent_id = ? WHERE project_id = ? AND id = ?", (parent_id, new_project_id, id_maps["scripts"][row["id"]]))
        for row in scripts.get("references") or []:
            script_id = _map_id(row.get("script_id"), id_maps["scripts"])
            ref_map = id_maps["worldbook_entries"] if row.get("ref_type") == "worldbook" else id_maps["characters"]
            ref_id = _map_id(row.get("ref_id"), ref_map)
            if not script_id or not ref_id:
                continue
            conn.execute(
                """INSERT INTO script_references (id, project_id, script_id, ref_type, ref_id, ref_name, description, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (new_id("ref"), new_project_id, script_id, row.get("ref_type"), ref_id, row.get("ref_name", ""), row.get("description", ""), stamp),
            )

        for row in presets:
            conn.execute(
                """INSERT INTO presets
                   (id, project_id, name, description, dimensions, custom_blocks, compiled_prompt, application_scenes, tags, category, ai_generated, generation_input, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_maps["presets"][row["id"]],
                    new_project_id,
                    row.get("name", "未命名预设"),
                    row.get("description", ""),
                    to_json_array(row.get("dimensions")),
                    to_json_array(row.get("custom_blocks")),
                    row.get("compiled_prompt", ""),
                    to_json_array(row.get("application_scenes")),
                    to_json_array(row.get("tags")),
                    row.get("category", "general"),
                    1 if row.get("ai_generated") else 0,
                    row.get("generation_input", ""),
                    stamp,
                    stamp,
                ),
            )

        entity_maps = {"worldbook_entry": "worldbook_entries", "character": "characters", "script": "scripts", "preset": "presets"}
        for row in versions:
            map_name = entity_maps.get(row.get("entity_type"))
            if not map_name:
                continue
            entity_id = _map_id(row.get("entity_id"), id_maps[map_name])
            if not entity_id:
                continue
            snapshot = _rewrite_snapshot(row.get("entity_type"), row.get("data"), new_project_id, id_maps)
            conn.execute(
                """INSERT INTO version_history (id, project_id, entity_type, entity_id, version, data, summary, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (version_id_map[row["id"]], new_project_id, row.get("entity_type"), entity_id, int(row.get("version") or 1), to_json(snapshot), row.get("summary", ""), row.get("created_at") or stamp),
            )

        target_maps = {"worldbook": "worldbook_entries", "character": "characters", "script": "scripts", "preset": "presets"}
        for row in ai_logs:
            map_name = target_maps.get(row.get("target_type"))
            target_id = _map_id(row.get("target_id"), id_maps[map_name]) if map_name else row.get("target_id", "")
            conn.execute(
                """INSERT INTO ai_operation_logs
                   (id, project_id, target_type, target_id, operation, status, section, field, instruction, prompt, request, response_preview, response_data, process_log, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    log_id_map[row["id"]],
                    new_project_id,
                    row.get("target_type", ""),
                    target_id or "",
                    row.get("operation", ""),
                    row.get("status", "success"),
                    row.get("section", ""),
                    row.get("field", ""),
                    row.get("instruction", ""),
                    row.get("prompt", ""),
                    to_json(row.get("request") or {}),
                    row.get("response_preview", ""),
                    to_json(row.get("response_data") if row.get("response_data") is not None else row.get("response_preview", "")),
                    to_json_array(row.get("process_log")),
                    row.get("created_at") or stamp,
                ),
            )

    return {"project_id": new_project_id, "project_name": new_project_name, "counts": preview["counts"], "id_maps": id_maps}
