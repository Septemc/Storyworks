"""Normalization helpers for worldbook factory payloads."""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_ENTRY_COUNT = 12
MIN_ENTRY_COUNT = 4
MAX_ENTRY_COUNT = 64
UNCLASSIFIED_LABEL = "未分类"

_CATEGORY_LABEL_MAP = {
    "geography": "地理",
    "location": "地理",
    "locations": "地理",
    "region": "地理",
    "regions": "地理",
    "faction": "势力",
    "factions": "势力",
    "organization": "势力",
    "organizations": "势力",
    "history": "历史",
    "historical": "历史",
    "rule": "规则",
    "rules": "规则",
    "law": "规则",
    "laws": "规则",
    "culture": "文化",
    "cultures": "文化",
    "character": "人物",
    "characters": "人物",
    "people": "人物",
    "npc": "人物",
}

_CATEGORY_PURPOSE_MAP = {
    "地理": "交代区域结构、地标与活动空间。",
    "势力": "说明组织目标、利益边界与对外关系。",
    "历史": "梳理起源、关键断裂与长期影响。",
    "规则": "明确代价、禁忌边界与运行逻辑。",
    "文化": "补充日常习俗、审美倾向与社会共识。",
    "人物": "沉淀关键角色、立场和代表性行为模式。",
    UNCLASSIFIED_LABEL: "补充尚未归类但对理解有帮助的设定。",
}

_STOP_WORDS = {
    "世界",
    "设定",
    "故事",
    "需要",
    "希望",
    "生成",
    "一个",
    "一些",
    "以及",
    "然后",
    "这个",
    "那个",
    "他们",
    "她们",
    "我们",
    "你们",
    "because",
    "about",
    "their",
    "world",
    "story",
    "setting",
}


def clamp_entry_count(value: Any) -> int:
    try:
        numeric = int(value)
    except Exception:
        numeric = DEFAULT_ENTRY_COUNT
    return max(MIN_ENTRY_COUNT, min(MAX_ENTRY_COUNT, numeric))


def ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value is None:
        return []
    return [value]


def clean_text(value: Any) -> str:
    return str(value or "").replace("\r", "\n").strip()


def normalize_category_name(value: Any) -> str:
    raw = clean_text(value)
    if not raw:
        return UNCLASSIFIED_LABEL
    return _CATEGORY_LABEL_MAP.get(raw.lower(), raw)


def category_purpose(category_name: str) -> str:
    normalized = normalize_category_name(category_name)
    return _CATEGORY_PURPOSE_MAP.get(normalized, f"补充“{normalized}”相关的稳定信息、关系和使用边界。")


def normalize_string_list(value: Any) -> list[str]:
    items: list[str] = []
    for item in ensure_list(value):
        text = clean_text(item)
        if text:
            items.append(text)
    return items


def normalize_tags(value: Any, *, fallback_category: str | None = None) -> list[str]:
    if isinstance(value, str):
        raw_items = [part.strip() for part in re.split(r"[,，/、\n]+", value) if part.strip()]
    else:
        raw_items = normalize_string_list(value)
    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    fallback = normalize_category_name(fallback_category)
    if fallback and fallback != UNCLASSIFIED_LABEL and fallback not in seen:
        normalized.insert(0, fallback)
    return normalized[:6]


def extract_seed_terms(*values: Any, limit: int = 8) -> list[str]:
    text = " ".join(clean_text(value) for value in values if clean_text(value))
    if not text:
        return []
    candidates = re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9_-]{3,15}", text)
    results: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        lowered = candidate.lower()
        if lowered in seen or lowered in _STOP_WORDS:
            continue
        seen.add(lowered)
        results.append(candidate)
        if len(results) >= limit:
            break
    return results


def resolve_worldbook_name(raw_name: Any, *fallback_values: Any) -> str:
    provided = clean_text(raw_name)
    if provided:
        return provided[:40]
    for value in fallback_values:
        text = clean_text(value)
        if not text:
            continue
        seed = re.split(r"[。！？!?;\n]+", text)[0].strip()
        if not seed:
            continue
        if len(seed) > 20:
            seed = seed[:20].rstrip("，,；;：:")
        if seed:
            return seed
    return "未命名世界书"


def allocate_counts(total: int, slots: int) -> list[int]:
    if slots <= 0:
        return []
    base = total // slots
    remainder = total % slots
    return [base + (1 if index < remainder else 0) for index in range(slots)]


def normalize_factory_request(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(payload or {})
    prompt = clean_text(source.get("user_prompt") or source.get("prompt"))
    description = clean_text(source.get("description"))
    language = clean_text(source.get("language")) or DEFAULT_LANGUAGE
    categories = [
        normalize_category_name(item)
        for item in ensure_list(source.get("desired_categories"))
        if clean_text(item)
    ]
    constraints = normalize_string_list(source.get("additional_constraints"))
    return {
        "user_prompt": prompt,
        "worldbook_name": resolve_worldbook_name(source.get("worldbook_name"), prompt, description),
        "description": description,
        "style": clean_text(source.get("style")) or "balanced",
        "language": language,
        "entry_count_hint": clamp_entry_count(source.get("entry_count_hint") or source.get("target_entry_count")),
        "desired_categories": categories,
        "additional_constraints": constraints,
    }


def normalize_blueprint_payload(
    payload: Mapping[str, Any] | None,
    *,
    fallback_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = normalize_factory_request(fallback_request)
    source = dict(payload or {})
    category_plan_raw = source.get("category_plan")
    category_plan: list[dict[str, Any]] = []
    if isinstance(category_plan_raw, list):
        for item in category_plan_raw:
            if not isinstance(item, Mapping):
                continue
            category_name = normalize_category_name(item.get("category"))
            category_plan.append(
                {
                    "category": category_name,
                    "target_entries": clamp_entry_count(item.get("target_entries") or 1),
                    "purpose": clean_text(item.get("purpose")) or category_purpose(category_name),
                    "focus": clean_text(item.get("focus")),
                    "keywords": normalize_string_list(item.get("keywords")),
                }
            )
    if not category_plan:
        desired = request["desired_categories"] or ["地理", "势力", "历史", "规则"]
        counts = allocate_counts(
            clamp_entry_count(source.get("entry_count_target") or request["entry_count_hint"]),
            len(desired),
        )
        category_plan = [
            {
                "category": normalize_category_name(name),
                "target_entries": max(1, counts[index] if index < len(counts) else 1),
                "purpose": category_purpose(name),
                "focus": "",
                "keywords": [],
            }
            for index, name in enumerate(desired)
        ]

    target_count = clamp_entry_count(
        source.get("entry_count_target")
        or sum(int(item.get("target_entries") or 0) for item in category_plan)
        or request["entry_count_hint"]
    )
    seed_terms = normalize_string_list(source.get("seed_terms")) or extract_seed_terms(
        request["user_prompt"],
        request["description"],
        *request["additional_constraints"],
    )
    return {
        "worldbook_name": resolve_worldbook_name(
            source.get("worldbook_name"),
            request["worldbook_name"],
            request["user_prompt"],
        ),
        "description": clean_text(source.get("description")) or request["description"],
        "style": clean_text(source.get("style")) or request["style"],
        "language": clean_text(source.get("language")) or request["language"],
        "prompt_summary": clean_text(source.get("prompt_summary")) or request["user_prompt"][:200],
        "entry_count_target": target_count,
        "seed_terms": seed_terms,
        "category_plan": category_plan,
        "additional_constraints": normalize_string_list(source.get("additional_constraints")) or request["additional_constraints"],
    }


def normalize_entry(
    item: Mapping[str, Any] | None,
    *,
    index: int,
    fallback_category: str,
    fallback_name: str,
) -> dict[str, Any]:
    source = dict(item or {})
    category_name = normalize_category_name(source.get("category") or fallback_category)
    title = clean_text(source.get("title")) or f"{fallback_name}设定条目 {index:02d}"
    content = clean_text(source.get("content")) or f"{title} 是 {fallback_name} 中需要补充完善的设定节点。"
    try:
        importance = float(source.get("importance", 0.6))
    except Exception:
        importance = 0.6
    importance = max(0.1, min(1.0, importance))
    meta = source.get("meta")
    meta_dict = dict(meta) if isinstance(meta, Mapping) else {}
    enabled = source.get("enabled")
    if enabled is None and isinstance(meta_dict.get("enabled"), bool):
        enabled = meta_dict.get("enabled")
    if enabled is None:
        enabled = True
    canonical = source.get("canonical")
    if canonical is None and isinstance(meta_dict.get("canonical"), bool):
        canonical = meta_dict.get("canonical")
    return {
        "entry_id": clean_text(source.get("entry_id")),
        "category": category_name,
        "title": title,
        "content": content,
        "importance": importance,
        "tags": normalize_tags(source.get("tags"), fallback_category=category_name),
        "enabled": bool(enabled),
        "canonical": bool(canonical),
        "meta": meta_dict,
    }


def normalize_worldbook_payload(
    payload: Mapping[str, Any] | None,
    *,
    blueprint: Mapping[str, Any] | None = None,
    fallback_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = dict(payload or {})
    request = normalize_factory_request(fallback_request)
    normalized_blueprint = normalize_blueprint_payload(blueprint, fallback_request=request) if blueprint is not None else None
    raw_entries = source.get("entries")
    if raw_entries is None and isinstance(source.get("payload"), Mapping):
        raw_entries = source["payload"].get("entries")

    fallback_category = normalized_blueprint["category_plan"][0]["category"] if normalized_blueprint and normalized_blueprint["category_plan"] else UNCLASSIFIED_LABEL
    fallback_name = resolve_worldbook_name(
        source.get("worldbook_name"),
        normalized_blueprint["worldbook_name"] if normalized_blueprint else request["worldbook_name"],
        request["worldbook_name"],
    )
    entries = [
        normalize_entry(
            item,
            index=index,
            fallback_category=fallback_category,
            fallback_name=fallback_name,
        )
        for index, item in enumerate(ensure_list(raw_entries), start=1)
        if isinstance(item, Mapping)
    ]
    return {
        "worldbook_name": fallback_name,
        "description": clean_text(source.get("description"))
        or (normalized_blueprint["description"] if normalized_blueprint else request["description"]),
        "language": clean_text(source.get("language"))
        or (normalized_blueprint["language"] if normalized_blueprint else request["language"]),
        "entry_count_target": clamp_entry_count(
            source.get("entry_count_target")
            or (normalized_blueprint["entry_count_target"] if normalized_blueprint else request["entry_count_hint"])
        ),
        "entries": entries,
        "meta": dict(source.get("meta")) if isinstance(source.get("meta"), Mapping) else {},
    }


def to_import_payload(
    payload: Mapping[str, Any] | None,
    *,
    worldbook_id: str | None = None,
) -> dict[str, Any]:
    normalized = normalize_worldbook_payload(payload)
    entries: list[dict[str, Any]] = []
    for index, entry in enumerate(normalized["entries"], start=1):
        meta = dict(entry.get("meta") or {})
        meta.setdefault("enabled", bool(entry.get("enabled", True)))
        meta.setdefault("disable", not bool(entry.get("enabled", True)))
        entries.append(
            {
                "entry_id": clean_text(entry.get("entry_id")) or f"wbf_entry_{index:03d}",
                "category": normalize_category_name(entry.get("category")),
                "title": clean_text(entry.get("title")),
                "content": clean_text(entry.get("content")),
                "importance": float(entry.get("importance") or 0.6),
                "tags": normalize_tags(entry.get("tags"), fallback_category=entry.get("category")),
                "canonical": bool(entry.get("canonical")),
                "meta": meta,
            }
        )
    result = {
        "worldbook_name": normalized["worldbook_name"],
        "entries": entries,
    }
    normalized_worldbook_id = clean_text(worldbook_id)
    if normalized_worldbook_id:
        result["worldbook_id"] = normalized_worldbook_id
    return result


def validate_import_payload_compatibility(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(payload or {})
    raw_entries = ensure_list(source.get("entries"))
    issues: list[str] = []
    warnings: list[str] = []
    normalized_entries = 0
    categories: set[str] = set()
    for index, raw in enumerate(raw_entries, start=1):
        if not isinstance(raw, Mapping):
            issues.append(f"第 {index} 条不是对象结构。")
            continue
        title = clean_text(raw.get("title"))
        content = clean_text(raw.get("content"))
        category = normalize_category_name(raw.get("category"))
        if not title:
            issues.append(f"第 {index} 条缺少 title。")
        if not content:
            issues.append(f"第 {index} 条缺少 content。")
        if len(content) < 24:
            warnings.append(f"第 {index} 条正文偏短，导入后信息量可能不足。")
        categories.add(category)
        normalized_entries += 1
    if normalized_entries < MIN_ENTRY_COUNT:
        warnings.append(f"当前仅有 {normalized_entries} 条条目，建议至少准备 {MIN_ENTRY_COUNT} 条。")
    if len(categories) <= 1 and normalized_entries > 0:
        warnings.append("当前条目集中在单一分类，检索时可能缺少横向覆盖。")
    return {
        "issues": issues,
        "warnings": list(dict.fromkeys(warnings)),
        "normalized_entry_count": normalized_entries,
        "category_count": len(categories),
    }


def first_non_empty(values: Iterable[Any], fallback: str = "") -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return fallback
