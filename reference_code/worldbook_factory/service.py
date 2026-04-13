"""Heuristic worldbook factory service."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from itertools import cycle
from typing import Any, Mapping

from apps.worldbook_factory.normalizer import (
    MIN_ENTRY_COUNT,
    UNCLASSIFIED_LABEL,
    allocate_counts,
    category_purpose,
    clamp_entry_count,
    extract_seed_terms,
    first_non_empty,
    normalize_blueprint_payload,
    normalize_category_name,
    normalize_factory_request,
    normalize_tags,
    normalize_worldbook_payload,
    to_import_payload,
    validate_import_payload_compatibility,
)
from apps.worldbook_factory.presenter import (
    build_workshop_overview,
    build_workshop_review,
)

BLUEPRINT_MODEL = "heuristic-worldbook-factory-blueprint-v1"
PAYLOAD_MODEL = "heuristic-worldbook-factory-payload-v1"
NORMALIZE_MODEL = "heuristic-worldbook-factory-normalize-v1"

_STYLE_HINTS = {
    "concise": "表达收束、信息密度高、句子更短。",
    "balanced": "表达平衡，兼顾清晰度与氛围。",
    "rich": "表达更饱满，强调氛围、牵连与代价。",
}

_CATEGORY_SCENE_HINTS = {
    "地理": ("空间骨架", "活动路径", "重要地标"),
    "势力": ("组织目标", "资源筹码", "对外摩擦"),
    "历史": ("起源事件", "断裂节点", "持续后果"),
    "规则": ("运行代价", "禁忌边界", "失控后果"),
    "文化": ("日常习俗", "价值偏好", "群体认同"),
    "人物": ("角色立场", "代表行为", "关系纽带"),
    UNCLASSIFIED_LABEL: ("核心设定", "使用方式", "边界说明"),
}

_RELATION_TEXTS = (
    "会牵动周边人的决策节奏",
    "直接改变资源与风险的分配",
    "常被视为判断阵营立场的试金石",
    "会在关键节点放大人物关系的张力",
)

_CONSEQUENCE_TEXTS = (
    "一旦失衡，局面会迅速转向更高代价的对抗。",
    "它看似稳定，实际上只在特定条件下成立。",
    "这条规则维持秩序的同时，也制造了新的灰色地带。",
    "表面上的平静通常只是更大冲突前的缓冲层。",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summarize_prompt(request: Mapping[str, Any]) -> str:
    prompt = str(request.get("user_prompt") or "").strip()
    description = str(request.get("description") or "").strip()
    if description:
        return f"{prompt}。补充定位：{description}" if prompt else description
    return prompt


def _resolve_categories(request: Mapping[str, Any], *, target_count: int) -> list[str]:
    desired = list(request.get("desired_categories") or [])
    categories = [normalize_category_name(item) for item in desired] if desired else []
    if not categories:
        extracted = extract_seed_terms(request.get("user_prompt"), request.get("description"), limit=4)
        categories = ["地理", "势力", "规则"] if extracted and target_count <= 6 else ["地理", "势力", "历史", "规则"]
    deduped: list[str] = []
    seen: set[str] = set()
    for item in categories:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped or [UNCLASSIFIED_LABEL]


def _build_blueprint(request_payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    request = normalize_factory_request(request_payload)
    if not request["user_prompt"]:
        raise ValueError("user_prompt_required")

    target_count = clamp_entry_count(request["entry_count_hint"])
    categories = _resolve_categories(request, target_count=target_count)
    counts = allocate_counts(target_count, len(categories))
    seed_terms = extract_seed_terms(
        request["worldbook_name"],
        request["user_prompt"],
        request["description"],
        *request["additional_constraints"],
        limit=8,
    )
    warnings: list[str] = []
    if request["entry_count_hint"] != target_count:
        warnings.append(f"目标条目数已自动收敛到 {target_count}。")
    if len(categories) == 1 and target_count >= MIN_ENTRY_COUNT:
        warnings.append("当前分类较少，建议后续至少保留两类信息面向，避免导入后结构过平。")

    category_plan: list[dict[str, Any]] = []
    for index, category in enumerate(categories):
        scene_hints = _CATEGORY_SCENE_HINTS.get(category, _CATEGORY_SCENE_HINTS[UNCLASSIFIED_LABEL])
        category_plan.append(
            {
                "category": category,
                "target_entries": max(1, counts[index] if index < len(counts) else 1),
                "purpose": category_purpose(category),
                "focus": f"优先覆盖 {scene_hints[0]}、{scene_hints[1]} 与 {scene_hints[2]}。",
                "keywords": seed_terms[index:index + 3] if seed_terms else [],
            }
        )

    blueprint = {
        "worldbook_name": request["worldbook_name"],
        "description": request["description"] or f"{request['worldbook_name']} 的基础蓝图。",
        "style": request["style"],
        "language": request["language"],
        "prompt_summary": _summarize_prompt(request),
        "entry_count_target": target_count,
        "seed_terms": seed_terms,
        "category_plan": category_plan,
        "additional_constraints": list(request["additional_constraints"]),
    }
    return blueprint, warnings


def generate_worldbook_blueprint(request_payload: Mapping[str, Any]) -> dict[str, Any]:
    blueprint, warnings = _build_blueprint(request_payload)
    overview = build_workshop_overview(
        blueprint=blueprint,
        payload=None,
        validation={"issues": [], "warnings": []},
        warnings=warnings,
    )
    return {
        "mode": "blueprint",
        "model": BLUEPRINT_MODEL,
        "target_entry_count": blueprint["entry_count_target"],
        "warnings": warnings,
        "blueprint": blueprint,
        "overview": overview,
        "review": build_workshop_review(
            blueprint=blueprint,
            payload=None,
            validation={"issues": [], "warnings": []},
            warnings=warnings,
        ),
    }


def _seed_for_slot(seed_terms: list[str], index: int, fallback: str) -> str:
    if seed_terms:
        return seed_terms[index % len(seed_terms)]
    return fallback


def _category_title(category: str, seed: str, slot_index: int) -> str:
    if category == "地理":
        variants = [f"{seed}港", f"{seed}边境", f"{seed}主城", f"{seed}航道"]
    elif category == "势力":
        variants = [f"{seed}盟约", f"{seed}议会", f"{seed}商团", f"{seed}卫队"]
    elif category == "历史":
        variants = [f"{seed}事变", f"{seed}旧约", f"{seed}断代", f"{seed}迁徙"]
    elif category == "规则":
        variants = [f"{seed}誓律", f"{seed}禁令", f"{seed}代价", f"{seed}仪轨"]
    elif category == "文化":
        variants = [f"{seed}节序", f"{seed}俗礼", f"{seed}行会习俗", f"{seed}共同记忆"]
    elif category == "人物":
        variants = [f"{seed}执灯人", f"{seed}守门者", f"{seed}见证者", f"{seed}调停人"]
    else:
        variants = [f"{seed}节点", f"{seed}条目", f"{seed}设定", f"{seed}侧写"]
    return variants[slot_index % len(variants)] if variants else f"{seed}设定 {slot_index + 1}"


def _entry_content(
    *,
    worldbook_name: str,
    category: str,
    title: str,
    seed: str,
    related_seed: str,
    style: str,
    focus: str,
    constraints: list[str],
    revision_notes: list[str] | None = None,
) -> str:
    relation = _RELATION_TEXTS[hash(title) % len(_RELATION_TEXTS)]
    consequence = _CONSEQUENCE_TEXTS[hash(seed + category) % len(_CONSEQUENCE_TEXTS)]
    constraint_line = f"设定约束上，需要同时满足“{constraints[0]}”。" if constraints else ""
    revision_line = f"本轮修订特别强化了：{revision_notes[0]}。" if revision_notes else ""
    sentences = [
        f"{title}是《{worldbook_name}》中与“{seed}”直接相关的{category}设定，重点承担{focus or category_purpose(category)}。",
        f"它通常与“{related_seed or seed}”形成联动，{relation}。",
        consequence,
        _STYLE_HINTS.get(style, _STYLE_HINTS["balanced"]),
        constraint_line,
        revision_line,
    ]
    return " ".join(sentence for sentence in sentences if sentence).strip()


def _build_entries_from_blueprint(
    blueprint_payload: Mapping[str, Any],
    *,
    style: str,
    constraints: list[str],
    revision_notes: list[str] | None = None,
) -> list[dict[str, Any]]:
    blueprint = normalize_blueprint_payload(blueprint_payload)
    seed_terms = list(blueprint.get("seed_terms") or []) or extract_seed_terms(
        blueprint["worldbook_name"],
        blueprint.get("prompt_summary"),
    )
    entries: list[dict[str, Any]] = []
    importance_cycle = cycle((0.92, 0.78, 0.64, 0.56))
    for category_index, category_item in enumerate(blueprint["category_plan"]):
        category = normalize_category_name(category_item.get("category"))
        target_entries = max(1, int(category_item.get("target_entries") or 1))
        focus = str(category_item.get("focus") or "").strip()
        keywords = list(category_item.get("keywords") or [])
        local_seed_terms = keywords or seed_terms or [category]
        for slot_index in range(target_entries):
            seed = _seed_for_slot(local_seed_terms, slot_index, category)
            related_seed = _seed_for_slot(seed_terms or local_seed_terms, category_index + slot_index + 1, seed)
            title = _category_title(category, seed, slot_index)
            entries.append(
                {
                    "entry_id": f"wbf_{category_index + 1:02d}_{slot_index + 1:02d}",
                    "category": category,
                    "title": title,
                    "content": _entry_content(
                        worldbook_name=blueprint["worldbook_name"],
                        category=category,
                        title=title,
                        seed=seed,
                        related_seed=related_seed,
                        style=style,
                        focus=focus,
                        constraints=constraints,
                        revision_notes=revision_notes,
                    ),
                    "importance": next(importance_cycle),
                    "tags": normalize_tags([category, seed, related_seed], fallback_category=category),
                    "enabled": True,
                    "canonical": slot_index == 0,
                    "meta": {
                        "factory": {
                            "source": "heuristic",
                            "generated_at": _utc_now_iso(),
                            "category_slot": category_index + 1,
                            "entry_slot": slot_index + 1,
                        },
                        "focus": focus,
                    },
                }
            )
    return entries


def _ensure_target_entry_count(
    entries: list[dict[str, Any]],
    *,
    target_count: int,
    blueprint: Mapping[str, Any],
    style: str,
    constraints: list[str],
    revision_notes: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    result = list(entries)
    if len(result) == target_count:
        return result, warnings
    if len(result) > target_count:
        warnings.append(f"条目数从 {len(result)} 条收敛到目标值 {target_count}。")
        return result[:target_count], warnings

    warnings.append(f"条目数不足，已自动补齐到目标值 {target_count}。")
    blueprint_normalized = normalize_blueprint_payload(blueprint)
    categories = [item.get("category") or UNCLASSIFIED_LABEL for item in blueprint_normalized["category_plan"]] or [UNCLASSIFIED_LABEL]
    seed_terms = blueprint_normalized.get("seed_terms") or [blueprint_normalized["worldbook_name"]]
    while len(result) < target_count:
        category = normalize_category_name(categories[len(result) % len(categories)])
        seed = seed_terms[len(result) % len(seed_terms)]
        title = _category_title(category, seed, len(result))
        result.append(
            {
                "entry_id": f"wbf_pad_{len(result) + 1:03d}",
                "category": category,
                "title": title,
                "content": _entry_content(
                    worldbook_name=blueprint_normalized["worldbook_name"],
                    category=category,
                    title=title,
                    seed=seed,
                    related_seed=seed_terms[(len(result) + 1) % len(seed_terms)],
                    style=style,
                    focus=category_purpose(category),
                    constraints=constraints,
                    revision_notes=revision_notes,
                ),
                "importance": 0.52,
                "tags": normalize_tags([category, seed], fallback_category=category),
                "enabled": True,
                "canonical": False,
                "meta": {
                    "factory": {
                        "source": "heuristic",
                        "generated_at": _utc_now_iso(),
                        "padded": True,
                    }
                },
            }
        )
    return result, warnings


def _assemble_payload_response(
    *,
    blueprint: Mapping[str, Any],
    payload: Mapping[str, Any],
    model: str,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    import_payload = to_import_payload(payload)
    validation = validate_import_payload_compatibility(import_payload)
    payload_normalized = normalize_worldbook_payload(payload, blueprint=blueprint)
    overview = build_workshop_overview(
        blueprint=blueprint,
        payload=payload_normalized,
        validation=validation,
        warnings=list(dict.fromkeys([*(warnings or []), *validation["warnings"]])),
    )
    review = build_workshop_review(
        blueprint=blueprint,
        payload=payload_normalized,
        validation=validation,
        warnings=list(dict.fromkeys([*(warnings or []), *validation["warnings"]])),
    )
    return {
        "mode": "payload",
        "model": model,
        "warnings": list(dict.fromkeys([*(warnings or []), *validation["warnings"]])),
        "target_entry_count": blueprint.get("entry_count_target") or payload_normalized["entry_count_target"],
        "actual_entry_count": len(payload_normalized["entries"]),
        "blueprint": normalize_blueprint_payload(blueprint),
        "payload": payload_normalized,
        "import_payload": import_payload,
        "import_validation": validation,
        "database_import_ready": not validation["issues"] and bool(import_payload.get("entries")),
        "overview": overview,
        "review": review,
    }


def generate_worldbook_from_blueprint(request_payload: Mapping[str, Any]) -> dict[str, Any]:
    request = normalize_factory_request(request_payload)
    blueprint = normalize_blueprint_payload(request_payload.get("blueprint"), fallback_request=request)
    style = request.get("style") or blueprint.get("style") or "balanced"
    constraints = list(request.get("additional_constraints") or blueprint.get("additional_constraints") or [])
    entries = _build_entries_from_blueprint(blueprint, style=style, constraints=constraints)
    entries, warnings = _ensure_target_entry_count(
        entries,
        target_count=blueprint["entry_count_target"],
        blueprint=blueprint,
        style=style,
        constraints=constraints,
    )
    payload = {
        "worldbook_name": blueprint["worldbook_name"],
        "description": first_non_empty(
            [request.get("description"), blueprint.get("description")],
            fallback=f"{blueprint['worldbook_name']} 的世界书条目集合。",
        ),
        "language": blueprint.get("language"),
        "entry_count_target": blueprint["entry_count_target"],
        "entries": entries,
        "meta": {
            "factory": {"generated_at": _utc_now_iso(), "source": "heuristic"},
            "style": style,
        },
    }
    return _assemble_payload_response(blueprint=blueprint, payload=payload, model=PAYLOAD_MODEL, warnings=warnings)


def generate_worldbook(request_payload: Mapping[str, Any]) -> dict[str, Any]:
    blueprint, blueprint_warnings = _build_blueprint(request_payload)
    result = generate_worldbook_from_blueprint({**dict(request_payload), "blueprint": blueprint})
    result["warnings"] = list(dict.fromkeys([*blueprint_warnings, *(result.get("warnings") or [])]))
    return result


def normalize_worldbook_result(request_payload: Mapping[str, Any]) -> dict[str, Any]:
    request = normalize_factory_request(request_payload)
    blueprint = normalize_blueprint_payload(request_payload.get("blueprint"), fallback_request=request)
    payload = normalize_worldbook_payload(
        request_payload.get("payload") if isinstance(request_payload.get("payload"), Mapping) else request_payload,
        blueprint=blueprint,
        fallback_request=request,
    )
    return _assemble_payload_response(
        blueprint=blueprint,
        payload=payload,
        model=NORMALIZE_MODEL,
        warnings=["结果已按导入结构重新规整。"],
    )


def revise_worldbook(request_payload: Mapping[str, Any]) -> dict[str, Any]:
    request = normalize_factory_request(request_payload)
    feedback_items = [
        str(item).strip()
        for item in (request_payload.get("feedback") or [])
        if str(item).strip()
    ]
    if not feedback_items:
        user_feedback = str(request_payload.get("user_feedback") or "").strip()
        if user_feedback:
            feedback_items = [segment.strip() for segment in user_feedback.replace("；", "\n").splitlines() if segment.strip()]
    if not feedback_items:
        raise ValueError("feedback_required")

    blueprint = normalize_blueprint_payload(request_payload.get("blueprint"), fallback_request=request)
    payload = normalize_worldbook_payload(
        request_payload.get("payload"),
        blueprint=blueprint,
        fallback_request=request,
    )
    revised_payload = copy.deepcopy(payload)
    revised_entries = list(revised_payload["entries"])
    for index, item in enumerate(revised_entries):
        note = feedback_items[index % len(feedback_items)]
        note_meta = dict(item.get("meta") or {})
        factory_meta = dict(note_meta.get("factory") or {})
        revision_notes = list(factory_meta.get("revision_notes") or [])
        if note not in revision_notes:
            revision_notes.append(note)
        factory_meta["revision_notes"] = revision_notes[:4]
        factory_meta["revised_at"] = _utc_now_iso()
        note_meta["factory"] = factory_meta
        item["meta"] = note_meta
        if note not in item["content"]:
            item["content"] = f"{item['content']} 本轮修订强化了“{note}”这一要求。".strip()

    target_count = clamp_entry_count(
        request_payload.get("target_entry_count") or payload.get("entry_count_target") or blueprint.get("entry_count_target")
    )
    revised_entries, warnings = _ensure_target_entry_count(
        revised_entries,
        target_count=target_count,
        blueprint=blueprint,
        style=request.get("style") or blueprint.get("style") or "balanced",
        constraints=list(request.get("additional_constraints") or blueprint.get("additional_constraints") or []),
        revision_notes=feedback_items,
    )
    revised_payload["entries"] = revised_entries
    revised_payload["entry_count_target"] = target_count
    revised_payload["description"] = first_non_empty(
        [request.get("description"), payload.get("description"), blueprint.get("description")],
        fallback=f"{blueprint['worldbook_name']} 修订版。",
    )
    revised_blueprint = copy.deepcopy(blueprint)
    revised_blueprint["entry_count_target"] = target_count
    revised_blueprint["additional_constraints"] = list(
        dict.fromkeys(
            [
                *(blueprint.get("additional_constraints") or []),
                *(request.get("additional_constraints") or []),
                *feedback_items,
            ]
        )
    )
    return _assemble_payload_response(
        blueprint=revised_blueprint,
        payload=revised_payload,
        model=PAYLOAD_MODEL,
        warnings=["已按反馈重写并重新检查导入兼容性。", *warnings],
    )
