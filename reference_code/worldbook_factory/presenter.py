"""Presentation helpers for worldbook factory responses."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


def _short_text(value: Any, *, limit: int = 88) -> str:
    text = " ".join(str(value or "").replace("\r", "\n").split()).strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _payload_entries(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    source = payload if isinstance(payload, Mapping) else {}
    entries = source.get("entries")
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, Mapping)]


def _blueprint_plan(blueprint: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    source = blueprint if isinstance(blueprint, Mapping) else {}
    category_plan = source.get("category_plan")
    if not isinstance(category_plan, list):
        return []
    return [item for item in category_plan if isinstance(item, Mapping)]


def _stage_label(*, has_payload: bool, import_ready: bool, has_issues: bool) -> str:
    if has_payload and import_ready:
        return "payload_ready"
    if has_payload and has_issues:
        return "payload_needs_attention"
    if has_payload:
        return "payload_review"
    return "blueprint_ready"


def _recommended_action(*, has_payload: bool, import_ready: bool, has_issues: bool) -> str:
    if not has_payload:
        return "继续生成条目"
    if has_issues:
        return "先处理导入问题"
    if import_ready:
        return "可以直接导入"
    return "先检查结果再导入"


def _build_suggested_feedback(
    *,
    actual_entry_count: int,
    target_entry_count: int,
    category_count: int,
    warnings: list[str],
    issues: list[str],
) -> list[str]:
    suggestions: list[str] = []
    if actual_entry_count < target_entry_count:
        suggestions.append("补足条目数量，并把关键分类的设定密度拉开。")
    if category_count <= 1:
        suggestions.append("增加横向分类，让世界书至少覆盖地理、势力或规则中的两类。")
    if any("正文偏短" in item for item in warnings):
        suggestions.append("把偏短条目的正文扩成可直接检索命中的描述。")
    if issues:
        suggestions.append("优先修复缺标题、缺正文或结构不兼容的条目。")
    if not suggestions:
        suggestions.append("可以按角色、规则代价和关键地点三条线继续细化。")
    return suggestions[:3]


def build_workshop_overview(
    *,
    blueprint: Mapping[str, Any] | None,
    payload: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    payload_entries = _payload_entries(payload)
    category_plan = _blueprint_plan(blueprint)
    validation_data = validation if isinstance(validation, Mapping) else {}
    issue_items = [str(item).strip() for item in (validation_data.get("issues") or []) if str(item).strip()]
    warning_items = [str(item).strip() for item in (warnings or []) if str(item).strip()]
    category_counts = Counter(str(item.get("category") or "未分类").strip() or "未分类" for item in payload_entries)
    target_entry_count = int((blueprint or {}).get("entry_count_target") or (payload or {}).get("entry_count_target") or 0)
    actual_entry_count = len(payload_entries)

    breakdown: list[dict[str, Any]] = []
    for item in category_plan:
        category_name = str(item.get("category") or "未分类").strip() or "未分类"
        breakdown.append(
            {
                "category": category_name,
                "target_entries": int(item.get("target_entries") or 0),
                "actual_entries": int(category_counts.get(category_name, 0)),
                "purpose": str(item.get("purpose") or "").strip(),
                "focus": str(item.get("focus") or "").strip(),
                "keywords": [str(keyword).strip() for keyword in (item.get("keywords") or []) if str(keyword).strip()],
            }
        )

    return {
        "worldbook_name": str((payload or {}).get("worldbook_name") or (blueprint or {}).get("worldbook_name") or "").strip(),
        "description": str((payload or {}).get("description") or (blueprint or {}).get("description") or "").strip(),
        "target_entry_count": target_entry_count,
        "actual_entry_count": actual_entry_count,
        "category_count": len({item["category"] for item in breakdown}) or len(category_counts),
        "categories": [item["category"] for item in breakdown],
        "seed_terms": [str(item).strip() for item in ((blueprint or {}).get("seed_terms") or []) if str(item).strip()],
        "category_breakdown": breakdown,
        "entry_preview": [
            {
                "entry_id": str(item.get("entry_id") or "").strip(),
                "title": str(item.get("title") or "").strip(),
                "category": str(item.get("category") or "未分类").strip() or "未分类",
                "content": _short_text(item.get("content"), limit=100),
                "importance": float(item.get("importance") or 0.0),
                "enabled": bool(item.get("enabled", True)),
                "canonical": bool(item.get("canonical", False)),
            }
            for item in payload_entries[:8]
        ],
        "import_ready": not issue_items and actual_entry_count > 0,
        "issue_count": len(issue_items),
        "warning_count": len(warning_items),
    }


def build_workshop_review(
    *,
    blueprint: Mapping[str, Any] | None,
    payload: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    overview = build_workshop_overview(
        blueprint=blueprint,
        payload=payload,
        validation=validation,
        warnings=warnings,
    )
    validation_data = validation if isinstance(validation, Mapping) else {}
    issues = [str(item).strip() for item in (validation_data.get("issues") or []) if str(item).strip()]
    warning_items = [str(item).strip() for item in (warnings or []) if str(item).strip()]
    stage = _stage_label(
        has_payload=bool(payload),
        import_ready=bool(overview["import_ready"]),
        has_issues=bool(issues),
    )
    return {
        "stage": stage,
        "recommended_action": _recommended_action(
            has_payload=bool(payload),
            import_ready=bool(overview["import_ready"]),
            has_issues=bool(issues),
        ),
        "import_hint": (
            "当前结果已经满足导入结构，可以直接写入世界书。"
            if overview["import_ready"]
            else "当前结果仍需检查，建议先修正问题或继续重写。"
        ),
        "checklist": [
            {
                "key": "blueprint",
                "label": "蓝图已建立",
                "status": "done" if blueprint else "pending",
                "detail": "分类规划已准备好。" if blueprint else "请先生成蓝图。",
            },
            {
                "key": "entries",
                "label": "条目已生成",
                "status": "done" if payload else "pending",
                "detail": f"当前共有 {overview['actual_entry_count']} 条条目。" if payload else "请继续生成条目。",
            },
            {
                "key": "validation",
                "label": "导入校验通过",
                "status": "done" if overview["import_ready"] else ("warning" if payload else "pending"),
                "detail": "当前可以直接导入。" if overview["import_ready"] else ("发现需要处理的问题。" if issues else "生成后会自动校验。"),
            },
        ],
        "suggested_feedback": _build_suggested_feedback(
            actual_entry_count=int(overview["actual_entry_count"] or 0),
            target_entry_count=int(overview["target_entry_count"] or 0),
            category_count=int(overview["category_count"] or 0),
            warnings=warning_items,
            issues=issues,
        ),
        "top_issues": issues[:4],
        "top_warnings": warning_items[:4],
    }
