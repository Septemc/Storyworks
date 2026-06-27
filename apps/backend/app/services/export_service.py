from __future__ import annotations

import json
import re
from typing import Any

from .character_schema import CHARACTER_SECTIONS, character_field_label, character_section_label


def safe_filename(value: str, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "_", value or "").strip("_")
    return cleaned or fallback


def markdown_value(value: Any, *, label_nested_keys: bool = False, depth: int = 0) -> str:
    if value is None or value == "":
        return "暂无"
    if isinstance(value, list):
        if not value:
            return "暂无"
        lines: list[str] = []
        for item in value:
            rendered = markdown_value(item, label_nested_keys=label_nested_keys, depth=depth + 1)
            if "\n" in rendered:
                lines.append("-")
                lines.extend([f"  {line}" for line in rendered.splitlines()])
            else:
                lines.append(f"- {rendered}")
        return "\n".join(lines)
    if isinstance(value, dict):
        if not value:
            return "暂无"
        lines = []
        for key, child in value.items():
            label = character_field_label(str(key)) if label_nested_keys else str(key)
            rendered = markdown_value(child, label_nested_keys=label_nested_keys, depth=depth + 1)
            if "\n" in rendered:
                lines.append(f"- **{label}**:")
                lines.extend([f"  {line}" for line in rendered.splitlines()])
            else:
                lines.append(f"- **{label}**: {rendered}")
        return "\n".join(lines)
    return str(value)


def export_characters_payload(rows: list[dict], export_format: str = "markdown") -> dict:
    if export_format == "json":
        return {"filename": "characters.json", "content": json.dumps(rows, ensure_ascii=False, indent=2)}

    lines = ["# 人物卡导出", ""]
    for char in rows:
        lines.extend([f"## {char['name']}", f"- 类型: {char.get('character_type', '')}", f"- 状态: {char.get('status', '')}", ""])
        developer = char.get("developer_data", {}) or {}
        ordered_sections = [section for section in CHARACTER_SECTIONS if section in developer]
        ordered_sections.extend([section for section in developer if section not in ordered_sections])
        for section in ordered_sections:
            content = developer.get(section)
            lines.append(f"### {character_section_label(str(section))}")
            if isinstance(content, dict):
                for key, value in content.items():
                    lines.append(f"- **{character_field_label(str(key))}**: {markdown_value(value, label_nested_keys=True)}")
            elif isinstance(content, list):
                lines.append(markdown_value(content, label_nested_keys=True))
            else:
                lines.append(markdown_value(content, label_nested_keys=True))
            lines.append("")
    return {"filename": "characters.md", "content": "\n".join(lines).strip() + "\n"}


def export_worldbook_payload(entries: list[dict], categories: list[dict], relations: list[dict], export_format: str = "markdown") -> dict:
    category_names = {item["id"]: item.get("name", "未分类") for item in categories}
    if export_format == "json":
        return {
            "filename": "worldbook.json",
            "content": json.dumps({"categories": categories, "entries": entries, "relations": relations}, ensure_ascii=False, indent=2),
        }

    lines = ["# 世界书导出", ""]
    for entry in entries:
        lines.append(f"## {entry['title']}")
        lines.append(f"- 分类: {category_names.get(entry.get('category_id'), '未分类')}")
        lines.append(f"- 状态: {entry.get('status', '')}")
        lines.append(f"- 可见性: {entry.get('visibility', '')}")
        lines.append(f"- 重要度: {entry.get('importance', '')}")
        if entry.get("tags"):
            lines.append(f"- 标签: {'、'.join(map(str, entry.get('tags') or []))}")
        if entry.get("creator"):
            lines.append(f"- 创建者: {entry.get('creator')}")
        lines.append("")
        if entry.get("content"):
            lines.extend([str(entry["content"]).strip(), ""])
        if entry.get("structured_data"):
            lines.extend(["### 结构化字段", markdown_value(entry["structured_data"]), ""])
        entry_relations = [rel for rel in relations if rel.get("source_id") == entry["id"] or rel.get("target_id") == entry["id"]]
        if entry_relations:
            lines.append("### 关联")
            for rel in entry_relations:
                if rel.get("source_id") == entry["id"]:
                    other = rel.get("target_title") or rel.get("target_id")
                    direction = "->"
                else:
                    other = rel.get("source_title") or rel.get("source_id")
                    direction = "<-"
                label = rel.get("label") or rel.get("relation_type", "related")
                lines.append(f"- {direction} {other}：{label}（强度 {rel.get('strength', '')}）")
            lines.append("")
    return {"filename": "worldbook.md", "content": "\n".join(lines).strip() + "\n"}


def export_project_payload(project: dict, payload: dict) -> dict:
    name = safe_filename(project.get("name", ""), "project")
    content = {
        "format_version": 1,
        "project": project,
        **payload,
    }
    return {"filename": f"{name}.storyworks.json", "content": json.dumps(content, ensure_ascii=False, indent=2)}
