from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from ..database import db, parse_json


DEFAULT_WORLDBOOK_TEMPLATE_SECTIONS = [
    {"id": "definition", "title": "定义", "required": True, "aiHint": "定义设定边界"},
    {"id": "history", "title": "历史源流", "required": False, "aiHint": "说明来源、演化和关键节点"},
    {"id": "rules", "title": "运行规则", "required": True, "aiHint": "说明规则、限制、代价和例外"},
    {"id": "relations", "title": "与角色/剧情的关系", "required": False, "aiHint": "说明与角色、剧本节点、冲突的连接方式"},
    {"id": "conflict", "title": "冲突点", "required": False, "aiHint": "指出可推动剧情的矛盾"},
    {"id": "hooks", "title": "可扩展钩子", "required": False, "aiHint": "给出可继续扩写的伏笔和用法"},
]


def clean_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip()


def worldbook_category_payload(project_id: str, category_id: str | None) -> dict | None:
    if not category_id:
        return None
    row = db.one("SELECT * FROM worldbook_categories WHERE project_id = ? AND id = ?", (project_id, category_id))
    if not row:
        return None
    row["template"] = parse_json(row.get("template"), {"sections": []})
    row["custom_fields"] = parse_json(row.get("custom_fields"), [])
    return row


def worldbook_template_sections(category: dict | None) -> list[dict]:
    template = category.get("template") if isinstance(category, dict) else {}
    sections = template.get("sections") if isinstance(template, dict) else []
    normalized: list[dict] = []
    for index, section in enumerate(sections if isinstance(sections, list) else []):
        if not isinstance(section, dict):
            continue
        title = clean_text(section.get("title") or section.get("name") or section.get("id"))
        if not title:
            continue
        section_id = clean_text(section.get("id") or section.get("key") or f"section_{index + 1}")
        normalized.append(
            {
                "id": section_id,
                "title": title,
                "required": bool(section.get("required", False)),
                "aiHint": clean_text(section.get("aiHint") or section.get("hint") or section.get("description")),
            }
        )
    return normalized or deepcopy(DEFAULT_WORLDBOOK_TEMPLATE_SECTIONS)


def worldbook_custom_field_keys(category: dict | None) -> list[str]:
    custom_fields = category.get("custom_fields") if isinstance(category, dict) else []
    keys: list[str] = []
    for index, field in enumerate(custom_fields if isinstance(custom_fields, list) else []):
        if isinstance(field, dict):
            key = clean_text(field.get("id") or field.get("key") or field.get("name") or field.get("title"))
        else:
            key = clean_text(field)
        keys.append(key or f"custom_{index + 1}")
    return keys


def markdown_heading_sections(content: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in (content or "").splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {title: "\n".join(lines).strip() for title, lines in sections.items()}


def worldbook_structured_from_content(category: dict | None, content: str) -> dict:
    heading_map = markdown_heading_sections(content)
    structured: dict[str, Any] = {}
    for section in worldbook_template_sections(category):
        title = section["title"]
        value = heading_map.get(title, "")
        if not value:
            value = heading_map.get(clean_text(section.get("id")), "")
        structured[section["id"]] = value
    for key in worldbook_custom_field_keys(category):
        structured.setdefault(key, "")
    return structured


def worldbook_template_prompt(category: dict | None) -> str:
    return json.dumps(
        {
            "sections": worldbook_template_sections(category),
            "custom_fields": worldbook_custom_field_keys(category),
        },
        ensure_ascii=False,
        indent=2,
    )
