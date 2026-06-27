from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from ..database import db, parse_json
from .character_schema import (
    CHARACTER_SECTIONS,
    normalize_character_field_name,
    normalize_developer_data,
)
from .character_service import ensure_character, update_character_payload
from .preset_service import update_preset_payload
from .script_service import update_script_payload
from .worldbook_service import update_worldbook_entry_payload


LEGACY_PREVIEW_LIMIT = 1600


def apply_ai_log_result(project_id: str, log_id: str) -> dict:
    log = db.one("SELECT * FROM ai_operation_logs WHERE project_id = ? AND id = ?", (project_id, log_id))
    if not log:
        raise HTTPException(status_code=404, detail="AI 历史不存在")
    if log.get("status") != "success" or log.get("operation") != "iterate":
        raise HTTPException(status_code=400, detail="只有成功的迭代历史可以应用")
    if not log.get("target_id"):
        raise HTTPException(status_code=400, detail="AI 历史缺少目标对象")

    result = resolve_log_result(log)
    target_type = log.get("target_type")
    if target_type == "worldbook":
        return {"target_type": target_type, "entity": apply_worldbook_log(project_id, log, result)}
    if target_type == "character":
        return {"target_type": target_type, "entity": apply_character_log(project_id, log, result)}
    if target_type == "script":
        return {"target_type": target_type, "entity": apply_script_log(project_id, log, result)}
    if target_type == "preset":
        return {"target_type": target_type, "entity": apply_preset_log(project_id, log, result)}
    raise HTTPException(status_code=400, detail=f"暂不支持应用 {target_type or '未知'} 类型的 AI 历史")


def resolve_log_result(log: dict) -> Any:
    result = parse_json(log.get("response_data"), None)
    if result is not None:
        return result
    preview = log.get("response_preview") or ""
    if not str(preview).strip():
        raise HTTPException(status_code=400, detail="AI 历史没有可应用结果")
    if len(str(preview)) >= LEGACY_PREVIEW_LIMIT:
        raise HTTPException(status_code=409, detail="这条旧历史只有截断预览，无法可靠应用；请重新执行一次迭代并保持直接保存开启。")
    parsed = parse_json(preview, None)
    return parsed if parsed is not None else preview


def apply_character_log(project_id: str, log: dict, result: Any) -> dict:
    payload = character_payload_from_log_result(result)
    if not payload.get("developer_data"):
        raise HTTPException(status_code=400, detail="AI 历史结果不是有效人物卡结构")
    target_id = str(log.get("target_id") or "")
    current = ensure_character(project_id, target_id)
    request = parse_json(log.get("request"), {})
    process_log = parse_json(log.get("process_log"), [])
    developer = merge_character_log_developer(
        current.get("developer_data") or {},
        payload["developer_data"],
        current.get("name") or "",
        log.get("section") or "",
        log.get("field") or "",
    )
    apply_payload = {
        "developer_data": developer,
        "summary": f"AI历史应用 {target_label(log)}",
        "ai_apply": {
            "prompt": log.get("prompt") or "",
            "result": developer,
            "section": log.get("section") or "",
            "field": log.get("field") or "",
            "instruction": log.get("instruction") or request.get("instruction") or "",
            "request": request,
            "process_log": process_log,
        },
    }
    if "field_visibility" in payload:
        apply_payload["field_visibility"] = payload["field_visibility"]
    if "player_data" in payload and not (log.get("section") or log.get("field")):
        apply_payload["player_data"] = payload["player_data"]
    return update_character_payload(project_id, target_id, apply_payload)


def apply_worldbook_log(project_id: str, log: dict, result: Any) -> dict:
    content = text_from_log_result(result)
    if not content:
        raise HTTPException(status_code=400, detail="AI 历史结果不是可保存的世界书正文")
    target_id = str(log.get("target_id") or "")
    return update_worldbook_entry_payload(
        project_id,
        target_id,
        {
            "content": content,
            "ai_prompt": log.get("prompt") or "",
            "summary": f"AI历史应用 {target_label(log)}",
            "ai_apply": apply_audit(log, content),
        },
    )


def apply_script_log(project_id: str, log: dict, result: Any) -> dict:
    content = text_from_log_result(result)
    if not content:
        raise HTTPException(status_code=400, detail="AI 历史结果不是可保存的剧本正文")
    target_id = str(log.get("target_id") or "")
    return update_script_payload(
        project_id,
        target_id,
        {
            "content": content,
            "ai_prompt": log.get("prompt") or "",
            "summary": f"AI历史应用 {target_label(log)}",
            "ai_apply": apply_audit(log, content),
        },
    )


def apply_preset_log(project_id: str, log: dict, result: Any) -> dict:
    payload = object_from_log_result(result)
    if not payload:
        raise HTTPException(status_code=400, detail="AI 历史结果不是可保存的预设结构")
    target_id = str(log.get("target_id") or "")
    return update_preset_payload(
        project_id,
        target_id,
        {
            **payload,
            "recompile": True,
            "summary": f"AI历史应用 {target_label(log)}",
            "ai_apply": apply_audit(log, payload),
        },
    )


def character_payload_from_log_result(result: Any) -> dict:
    if not isinstance(result, dict):
        return {}
    if isinstance(result.get("character"), dict):
        result = result["character"]
    has_sections = any(section in result for section in CHARACTER_SECTIONS)
    developer = result.get("developer_data") or (result if has_sections else None)
    if not isinstance(developer, dict):
        return {}
    payload = {"developer_data": developer}
    if isinstance(result.get("player_data"), dict):
        payload["player_data"] = result["player_data"]
    if isinstance(result.get("field_visibility"), dict):
        payload["field_visibility"] = result["field_visibility"]
    return payload


def merge_character_log_developer(base: dict, incoming: dict, fallback_name: str = "", only_section: str = "", only_field: str = "") -> dict:
    merged = normalize_developer_data(base or {}, fallback_name, "")
    incoming_data = incoming if isinstance(incoming, dict) else {}
    only_section = normalize_log_section(only_section)
    only_field = normalize_character_field_name(only_field)
    for section in CHARACTER_SECTIONS:
        if only_section and section != only_section:
            continue
        if section not in incoming_data:
            continue
        value = incoming_data.get(section)
        if section in ("relations", "inventory", "skills"):
            if only_field:
                continue
            if isinstance(value, list):
                merged[section] = value
            elif value not in (None, "", [], {}):
                merged[section] = [value]
            continue
        if section == "extras":
            if not only_field and value not in (None, "", [], {}):
                merged[section] = value if isinstance(value, str) else str(value)
            continue
        if isinstance(merged.get(section), dict) and isinstance(value, dict):
            for raw_field, field_value in value.items():
                field = normalize_character_field_name(raw_field)
                if only_field and field != only_field:
                    continue
                if field_value not in (None, "", [], {}):
                    merged[section][field] = field_value
    return normalize_developer_data(merged, fallback_name, "")


def normalize_log_section(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if lowered in CHARACTER_SECTIONS:
        return lowered
    labels = {
        "基础": "basic",
        "信息": "knowledge",
        "隐秘": "secrets",
        "属性": "attributes",
        "关系": "relations",
        "物品": "inventory",
        "技能": "skills",
        "命运": "fortune",
        "补充": "extras",
    }
    for label, section in labels.items():
        if label in text or section.upper() in text.upper():
            return section
    return ""


def text_from_log_result(result: Any) -> str:
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, dict):
        for key in ("content", "generated", "text"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def object_from_log_result(result: Any) -> dict:
    if not isinstance(result, dict) or isinstance(result, list):
        return {}
    if isinstance(result.get("generated"), dict):
        return result["generated"]
    if isinstance(result.get("fixed_preset"), dict):
        return result["fixed_preset"]
    return result


def apply_audit(log: dict, result: Any) -> dict:
    request = parse_json(log.get("request"), {})
    return {
        "prompt": log.get("prompt") or "",
        "result": result,
        "section": log.get("section") or "",
        "field": log.get("field") or "",
        "instruction": log.get("instruction") or request.get("instruction") or "",
        "request": request,
        "process_log": parse_json(log.get("process_log"), []),
    }


def target_label(log: dict) -> str:
    return " / ".join(item for item in [log.get("section"), log.get("field")] if item) or "全部"
