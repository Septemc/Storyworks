from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException

from ..database import compile_preset, db, parse_json, project_or_404
from ..services.ai_service import (
    append_log,
    call_ai_with_logging,
    clean_text,
    extract_json_object,
    generation_log,
    record_ai_operation,
    replace_markdown_section,
    strip_ai_markdown_preamble,
)
from ..services.character_schema import (
    CHARACTER_SECTIONS,
    CHARACTER_LIST_ITEM_SCHEMAS,
    CHARACTER_SECTION_LABELS,
    DEFAULT_CHARACTER_DEVELOPER,
    apply_player_visibility as apply_character_player_visibility,
    character_contract_template,
    character_section_for_field,
    default_character_data as default_character_schema_data,
    normalize_character_contract,
    normalize_character_field_name,
    normalize_developer_data,
    normalize_visibility,
)
from ..services.character_service import (
    ensure_character as service_ensure_character,
    get_character as service_get_character,
    get_character_detail as service_get_character_detail,
    list_characters as service_list_characters,
    update_character_payload as service_update_character,
)
from ..services.preset_service import (
    get_preset as service_get_preset,
    update_preset_payload as service_update_preset,
)
from ..services.project_service import normalize_project_settings
from ..services.script_service import (
    ensure_script as service_ensure_script,
    get_script as service_get_script,
    get_script_detail as service_get_script_detail,
    list_scripts as service_list_scripts,
    update_script_payload as service_update_script,
)
from ..services.version_service import current_version_entity as service_current_version_entity
from ..services.worldbook_service import (
    ensure_worldbook_entry as service_ensure_worldbook_entry,
    get_worldbook_entry as service_get_worldbook_entry,
    get_worldbook_entry_detail as service_get_worldbook_entry_detail,
    list_worldbook_categories,
    list_worldbook_entries,
    update_worldbook_entry_payload as service_update_worldbook_entry,
)
from ..services.worldbook_schema import (
    worldbook_category_payload,
    worldbook_custom_field_keys,
    worldbook_structured_from_content,
    worldbook_template_prompt,
    worldbook_template_sections,
)


router = APIRouter()


def ok(data: Any = None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


def require_row(row: Optional[dict], message: str):
    if row is None:
        raise HTTPException(status_code=404, detail=message)
    return row


def list_categories(project_id: str):
    return list_worldbook_categories(project_id)


def get_worldbook_entry(project_id: str, entry_id: str):
    return service_get_worldbook_entry(project_id, entry_id)


def get_character(project_id: str, character_id: str):
    return service_get_character(project_id, character_id)


def project_ai_call_options(project_id: str, data: dict, default_max_tokens: int) -> dict:
    project = project_or_404(project_id)
    settings = normalize_project_settings(parse_json(project.get("settings"), {}))
    ai_settings = settings.get("ai", {})
    temperature = data.get("temperature")
    max_tokens = data.get("max_tokens") or data.get("maxTokens")
    return {
        "temperature": temperature if temperature is not None else ai_settings.get("temperature", 0.7),
        "max_tokens": resolve_project_max_tokens(max_tokens, ai_settings.get("max_tokens"), default_max_tokens),
    }


def resolve_project_max_tokens(requested: Any, project_default: Any, endpoint_default: int) -> int:
    for value in (requested, project_default):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        return max(endpoint_default, min(parsed, 20000))
    return endpoint_default


def get_script(project_id: str, script_id: str):
    return service_get_script(project_id, script_id)


def get_preset(project_id: str, preset_id: str):
    return service_get_preset(project_id, preset_id)


def ensure_world_entry(project_id: str, entry_id: str):
    return service_ensure_worldbook_entry(project_id, entry_id)


def ensure_character(project_id: str, character_id: str):
    return service_ensure_character(project_id, character_id)


def ensure_script(project_id: str, script_id: str):
    return service_ensure_script(project_id, script_id)


def worldbook_entries(project_id: str, category_id: Optional[str] = None, status: Optional[str] = None, q: str = "", tag: str = "", min_importance: int = 1):
    return ok(list_worldbook_entries(project_id, category_id=category_id, status=status, q=q, tag=tag, min_importance=min_importance))


def worldbook_entry(project_id: str, entry_id: str):
    return ok(service_get_worldbook_entry_detail(project_id, entry_id))


def update_worldbook_entry(project_id: str, entry_id: str, data: dict = Body(...)):
    return ok(service_update_worldbook_entry(project_id, entry_id, data), "条目更新成功")


def characters(project_id: str, q: str = "", character_type: str = "", status: str = "", tag: str = ""):
    return ok(service_list_characters(project_id, q=q, character_type=character_type, status=status, tag=tag))


def character(project_id: str, character_id: str):
    return ok(service_get_character_detail(project_id, character_id))


def update_character(project_id: str, character_id: str, data: dict = Body(...)):
    return ok(service_update_character(project_id, character_id, data), "角色更新成功")


def scripts(project_id: str, node_type: str = "", status: str = "", q: str = ""):
    return ok(service_list_scripts(project_id, node_type=node_type, status=status, q=q))


def script(project_id: str, script_id: str):
    return ok(service_get_script_detail(project_id, script_id))


def update_script(project_id: str, script_id: str, data: dict = Body(...)):
    return ok(service_update_script(project_id, script_id, data), "节点更新成功")


def preset(project_id: str, preset_id: str):
    return ok(require_row(service_get_preset(project_id, preset_id), "预设不存在"))


def update_preset(project_id: str, preset_id: str, data: dict = Body(...)):
    return ok(service_update_preset(project_id, preset_id, data), "预设更新成功")

def build_ai_apply_payload(
    prompt: str,
    result: Any,
    *,
    section: str = "",
    field: str = "",
    instruction: str = "",
    request: Optional[dict] = None,
    process_log: Optional[list] = None,
    summary: str = "",
) -> dict:
    target = " / ".join(item for item in [clean_text(section), clean_text(field)] if item)
    return {
        "summary": summary or f"AI迭代 {target or '全文'}",
        "ai_apply": {
            "prompt": prompt,
            "result": result,
            "section": clean_text(section),
            "field": clean_text(field),
            "instruction": clean_text(instruction),
            "request": request if isinstance(request, dict) else {},
            "process_log": process_log if isinstance(process_log, list) else [],
        },
    }


def next_version_number(project_id: str, entity_type: str, entity_id: str) -> int:
    row = db.one(
        "SELECT COALESCE(MAX(version), 0) + 1 AS version FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ?",
        (project_id, entity_type, entity_id),
    )
    return int(row["version"] or 1)


def default_character_data(name: str, concept: str = ""):
    return default_character_schema_data(name, concept)


def apply_player_visibility(developer_data: dict, visibility: dict):
    return apply_character_player_visibility(developer_data, visibility)


def current_version_entity(project_id: str, entity_type: str, entity_id: str) -> dict:
    return service_current_version_entity(project_id, entity_type, entity_id)


def normalize_character_payload(parsed: Optional[dict], fallback_name: str, fallback_text: str = "") -> dict:
    if not parsed:
        developer, player, visibility = default_character_data(fallback_name or "未命名角色", fallback_text)
        return {"name": fallback_name or "未命名角色", "developer_data": developer, "player_data": player, "field_visibility": visibility, "tags": []}

    developer = parsed.get("developer_data") or parsed.get("developer") or {}
    if "basic" not in developer and any(key in parsed for key in CHARACTER_SECTIONS):
        developer = {section: parsed.get(section) for section in CHARACTER_SECTIONS if section in parsed}

    developer = normalize_developer_data(developer, fallback_name or "", fallback_text)
    basic = developer.setdefault("basic", {})
    name = clean_text(basic.get("name") or parsed.get("name") or fallback_name or "未命名角色")
    basic["name"] = name
    basic.setdefault("gender", clean_text(parsed.get("gender") or ""))
    visibility = normalize_visibility(developer, parsed.get("field_visibility") or parsed.get("visibility") or {})
    player = parsed.get("player_data") or apply_player_visibility(developer, visibility)
    normalized = normalize_character_contract({"name": name, "developer_data": developer, "player_data": player, "field_visibility": visibility})
    return {
        "name": name,
        "character_type": parsed.get("character_type", "supporting"),
        "developer_data": normalized["developer_data"],
        "player_data": normalized["player_data"],
        "field_visibility": normalized["field_visibility"],
        "tags": parsed.get("tags") or [],
        "generation_history": parsed.get("generation_history") or [],
    }


CHARACTER_SECTION_ALIASES = {
    "基础": "basic",
    "基础信息": "basic",
    "信息": "knowledge",
    "知识": "knowledge",
    "隐秘": "secrets",
    "秘密": "secrets",
    "属性": "attributes",
    "关系": "relations",
    "物品": "inventory",
    "装备": "inventory",
    "库存": "inventory",
    "技能": "skills",
    "能力": "skills",
    "命运": "fortune",
    "补充": "extras",
    "备注": "extras",
}


CHARACTER_INSTRUCTION_FIELD_CUES = [
    ("basic", "summary", ("人物描述", "角色描述", "人物简介", "角色简介", "简介", "摘要", "summary", "description")),
    ("basic", "status", ("当前状态", "境界", "修为", "等级", "level", "status")),
    ("basic", "identity", ("身份", "职业", "identity")),
    ("knowledge", "appearance", ("外观", "外貌", "形象", "appearance")),
    ("knowledge", "personality", ("性格", "人格", "personality")),
    ("knowledge", "background", ("背景", "经历", "身世", "background")),
    ("knowledge", "motivation", ("动机", "目标", "motivation")),
    ("secrets", "privateTruth", ("隐秘真相", "私下真相", "秘密", "privateTruth")),
    ("secrets", "hiddenAgenda", ("隐藏目标", "真实目标", "hiddenAgenda")),
    ("attributes", "limitations", ("限制代价", "健康", "伤势", "旧伤", "health", "limitations")),
]

CHARACTER_INSTRUCTION_SECTION_CUES = [
    ("secrets", ("隐秘字段", "隐秘部分", "隐秘", "秘密", "SECRETS")),
    ("attributes", ("属性字段", "属性部分", "属性", "ATTRIBUTES")),
    ("relations", ("关系字段", "关系部分", "人物关系", "关系", "RELATIONS")),
    ("inventory", ("物品字段", "物品部分", "装备", "物品", "INVENTORY")),
    ("skills", ("技能字段", "技能部分", "技能", "能力", "SKILLS")),
    ("fortune", ("命运字段", "命运部分", "命运", "FORTUNE")),
    ("extras", ("补充字段", "补充部分", "补充", "备注", "EXTRAS")),
]


def normalize_character_section_key(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    lowered = text.lower()
    if lowered in CHARACTER_SECTIONS:
        return lowered
    for key, label in CHARACTER_SECTION_LABELS.items():
        if text == label or text in label or key.upper() in text.upper():
            return key
    return CHARACTER_SECTION_ALIASES.get(text, "")


def normalize_character_field_key(value: Any) -> str:
    return normalize_character_field_name(value)


def infer_character_target_from_instruction(instruction: str, log: list[dict]) -> tuple[str, str]:
    text = clean_text(instruction)
    if not text:
        return "", ""
    lowered = text.lower()
    field_matches: list[tuple[str, str, str]] = []
    for section, field, cues in CHARACTER_INSTRUCTION_FIELD_CUES:
        matched = next((cue for cue in cues if cue.lower() in lowered), "")
        if matched:
            field_matches.append((section, field, matched))
    unique_fields = {(section, field) for section, field, _ in field_matches}
    if len(unique_fields) == 1:
        section, field, cue = field_matches[0]
        append_log(log, f"根据迭代要求「{cue}」自动定位到分类 {section}.{field}")
        return section, field

    section_matches: list[tuple[str, str]] = []
    for section, cues in CHARACTER_INSTRUCTION_SECTION_CUES:
        matched = next((cue for cue in cues if cue.lower() in lowered), "")
        if matched:
            section_matches.append((section, matched))
    unique_sections = {section for section, _ in section_matches}
    if len(unique_sections) == 1:
        section, cue = section_matches[0]
        append_log(log, f"根据迭代要求「{cue}」自动定位到分类 {section}")
        return section, ""
    if field_matches or section_matches:
        append_log(log, "迭代要求中出现多个可能目标，保持整体迭代以避免误写字段")
    return "", ""


def is_blank_character_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False


def character_developer_from_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {}
    developer = payload.get("developer_data")
    if isinstance(developer, dict):
        return developer
    if any(section in payload for section in CHARACTER_SECTIONS):
        return {section: payload.get(section) for section in CHARACTER_SECTIONS if section in payload}
    partial: dict[str, dict] = {}
    for raw_key, value in payload.items():
        field = normalize_character_field_key(raw_key)
        section = character_section_for_field(field)
        if section and not is_blank_character_value(value):
            partial.setdefault(section, {})[field] = value
    return partial


def character_contract_issues(payload: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict):
        return ["输出不是 JSON 对象"]
    developer = character_developer_from_payload(payload)
    if not developer:
        return ["缺少 developer_data 或 9 大人物卡分类"]
    for section in CHARACTER_SECTIONS:
        if section not in developer:
            issues.append(f"缺少分类 {section}")
            continue
        value = developer.get(section)
        expected = DEFAULT_CHARACTER_DEVELOPER[section]
        if isinstance(expected, dict):
            if not isinstance(value, dict):
                issues.append(f"分类 {section} 必须是对象")
                continue
            normalized_fields = {normalize_character_field_key(raw_field) for raw_field in value}
            for field in expected:
                if field not in normalized_fields:
                    issues.append(f"分类 {section} 缺少字段 {field}")
            for raw_field in value:
                if normalize_character_field_key(raw_field) not in expected:
                    issues.append(f"分类 {section} 包含非契约字段 {raw_field}")
        elif isinstance(expected, list):
            if not isinstance(value, list):
                issues.append(f"分类 {section} 必须是数组")
                continue
            schema = CHARACTER_LIST_ITEM_SCHEMAS.get(section)
            if schema and not value:
                issues.append(f"分类 {section} 至少需要 1 项，并使用固定小字段")
                continue
            if schema:
                for index, item in enumerate(value):
                    if not isinstance(item, dict):
                        issues.append(f"分类 {section} 第 {index + 1} 项必须是对象")
                        continue
                    for field in schema:
                        if field not in item:
                            issues.append(f"分类 {section} 第 {index + 1} 项缺少字段 {field}")
        elif section == "extras" and not isinstance(value, str):
            issues.append("分类 extras 必须是纯文本字符串")
    basic = developer.get("basic") if isinstance(developer.get("basic"), dict) else {}
    if is_blank_character_value(basic.get("name")):
        issues.append("basic.name 不能为空，未指定姓名时也必须生成合适姓名")
    if is_blank_character_value(basic.get("gender")):
        issues.append("basic.gender 不能为空")
    if is_blank_character_value(basic.get("summary")):
        issues.append("basic.summary 不能为空")
    return issues


def character_contract_prompt() -> str:
    return json.dumps(
        {
            "character_type": "protagonist|supporting|antagonist|npc",
            "developer_data": character_contract_template(),
            "field_visibility": {},
            "tags": ["标签"],
        },
        ensure_ascii=False,
        indent=2,
    )


async def repair_character_generation_payload(project_id: str, data: dict, log: list[dict], raw_text: str, parsed: Any) -> tuple[Any, list[str]]:
    issues = character_contract_issues(parsed)
    current_text = raw_text
    current_parsed = parsed
    for attempt in range(2):
        if not issues:
            break
        append_log(log, f"格式审查发现 {len(issues)} 个问题，执行第 {attempt + 1} 次结构修复")
        repair_prompt = f"""你需要把模型输出修复为 Storyworks 人物卡严格 JSON。
用户原始提示词仅作为角色内容参考，不允许改变字段契约。

用户指定姓名: {data.get('name') or '未指定'}
角色类型: {data.get('character_type', 'supporting')}
用户提示词:
{data.get('concept') or data.get('prompt') or ''}

上一轮模型输出:
{current_text}

格式问题:
{json.dumps(issues, ensure_ascii=False)}

必须输出完整 JSON，且只能使用以下 9 个 developer_data 分类和既定字段，不要新增大类，不要把自由提示词当字段名:
{character_contract_prompt()}

要求:
1. 只输出 JSON 对象，不输出解释、Markdown 或代码块。
2. 所有分类和字段都必须存在；extras 必须是纯文本字符串。
3. relations、inventory、skills 必须是数组，数组内每一项都必须使用模板给出的固定小字段。
4. 尽量保留上一轮输出中的有效内容，缺失内容按用户提示词和项目背景补齐。
5. 修仙、都市、科幻或其他题材差异只能写入字段内容，不能改变字段结构。"""
        current_text = await call_ai_with_logging(
            project_id,
            "character",
            "generate_repair",
            repair_prompt,
            "你是 Storyworks 人物卡结构化修复器，只输出严格 JSON。",
            request={**data, "repair_issues": issues},
            process_log=log,
            temperature=0.1,
            max_tokens=14000,
        )
        current_parsed = extract_json_object(current_text)
        issues = character_contract_issues(current_parsed)
    return current_parsed, issues


def merge_character_developer(base: dict, incoming: Any, fallback_name: str = "", only_section: str = "", only_field: str = "") -> dict:
    merged = deepcopy(base) if isinstance(base, dict) else {}
    merged = normalize_developer_data(merged, fallback_name, "")
    incoming_data = character_developer_from_payload(incoming) if isinstance(incoming, dict) else {}
    if not incoming_data:
        return merged
    only_section = normalize_character_section_key(only_section)
    only_field = normalize_character_field_key(only_field)
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
            elif not is_blank_character_value(value):
                merged[section] = [value]
        elif section == "extras":
            if only_field:
                continue
            if not is_blank_character_value(value):
                merged[section] = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        elif isinstance(merged.get(section), dict) and isinstance(value, dict):
            for raw_field, field_value in value.items():
                field = normalize_character_field_key(raw_field)
                if only_field and field != only_field:
                    continue
                if not is_blank_character_value(field_value):
                    merged[section][field] = field_value
    return normalize_developer_data(merged, fallback_name, "")


async def repair_character_iteration_payload(
    project_id: str,
    char: dict,
    data: dict,
    log: list[dict],
    raw_text: str,
    parsed: Any,
) -> Any:
    issues = character_contract_issues(parsed)
    if not issues:
        return parsed
    append_log(log, f"整体迭代结果结构不完整，执行结构修复")
    repair_prompt = f"""你需要把角色迭代输出修复为完整 developer_data JSON。
只能使用 Storyworks 9 大人物卡分类和既定字段。

角色名称: {char.get('name')}
迭代要求:
{data.get('instruction') or ''}

当前 developer_data:
{json.dumps(char.get('developer_data') or {}, ensure_ascii=False)}

上一轮模型输出:
{raw_text}

格式问题:
{json.dumps(issues, ensure_ascii=False)}

严格 developer_data 契约:
{json.dumps(character_contract_template(), ensure_ascii=False, indent=2)}

只输出完整 developer_data JSON，不要输出解释；relations、inventory、skills 的数组项必须使用模板中的固定小字段。"""
    repair_text = await call_ai_with_logging(
        project_id,
        "character",
        "iterate_repair",
        repair_prompt,
        "你是 Storyworks 人物卡迭代结构化修复器，只输出严格 JSON。",
        target_id=char.get("id", ""),
        instruction=clean_text(data.get("instruction")),
        request={**data, "repair_issues": issues},
        process_log=log,
        temperature=0.1,
        max_tokens=14000,
    )
    return extract_json_object(repair_text) or {}

@router.post("/api/projects/{project_id}/worldbook/ai/generate")
async def ai_generate_worldbook(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    log = generation_log("校验项目与分类", "读取同项目世界书上下文")
    category = worldbook_category_payload(project_id, data.get("category_id"))
    category_name = category["name"] if category else "未分类"
    context_rows = db.all("SELECT title, content FROM worldbook_entries WHERE project_id = ? AND (? = '' OR category_id = ?) ORDER BY updated_at DESC LIMIT 10", (project_id, data.get("category_id") or "", data.get("category_id") or ""))
    context = "\n".join([f"- {r['title']}: {(r.get('content') or '')[:260]}" for r in context_rows])
    append_log(log, "组装世界书生成提示词")
    prompt = f"""请生成一个世界书条目。
分类: {category_name}
标题: {data.get('title') or '由你生成'}
用户要求: {data.get('prompt', '')}
分类模板和结构化字段约束:
{worldbook_template_prompt(category)}

已有世界观参考:
{context or '暂无'}

请输出 Markdown 正文，必须满足：
1. 使用分类模板中的 sections 作为二级标题，标题文字必须与模板 title 完全一致。
2. required=true 的板块必须有具体内容，不要空泛。
3. custom_fields 不要作为 Markdown 标题强行输出，但正文应提供足够信息供结构化字段引用。
4. 保持与同分类上下文一致，补充可被角色、剧本和预设复用的设定细节。
字数控制在 {data.get('min_length', 800)}-{data.get('max_length', 1800)} 字，不要截断。"""
    append_log(log, "调用 AI 模型生成正文")
    content = await call_ai_with_logging(project_id, "worldbook", "generate", prompt, "你是专业世界观设定助手，重视一致性、可写性和结构化表达。", request=data, process_log=log, **project_ai_call_options(project_id, data, 12000))
    structured_data = worldbook_structured_from_content(category, content)
    ai_metadata = {"category_template": worldbook_template_sections(category), "custom_fields": worldbook_custom_field_keys(category)}
    append_log(log, "生成完成，返回可编辑正文和结构化字段")
    record_ai_operation(project_id, "worldbook", "generate", prompt, {"content": content, "structured_data": structured_data}, request=data, process_log=log)
    return ok(
        {
            "title": data.get("title") or "AI生成条目",
            "category_id": data.get("category_id"),
            "content": content,
            "structured_data": structured_data,
            "ai_metadata": ai_metadata,
            "ai_prompt": prompt,
            "generation_log": log,
        },
        "生成成功",
    )


@router.post("/api/projects/{project_id}/worldbook/entries/{entry_id}/ai/iterate")
async def ai_iterate_worldbook_entry(project_id: str, entry_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    entry = ensure_world_entry(project_id, entry_id)
    section = clean_text(data.get("section"))
    instruction = clean_text(data.get("instruction"), "在保持既有设定一致的前提下，补充细节并提升可用性。")
    log = generation_log("读取当前世界书条目", "读取相关世界书关系与上下文")
    relations = worldbook_entry(project_id, entry_id)["data"].get("relations", [])
    context_rows = db.all("SELECT title, content FROM worldbook_entries WHERE project_id = ? AND id != ? ORDER BY updated_at DESC LIMIT 8", (project_id, entry_id))
    context = "\n".join([f"- {r['title']}: {(r.get('content') or '')[:220]}" for r in context_rows])
    append_log(log, "组装迭代提示词")
    prompt = f"""请对已有世界书条目执行 AI 迭代。
条目标题: {entry['title']}
目标板块: {section or '全文'}
迭代要求: {instruction}
现有正文:
{entry.get('content') or ''}

结构化字段:
{json.dumps(entry.get('structured_data') or {}, ensure_ascii=False)}

现有关联:
{json.dumps(relations, ensure_ascii=False)}

同项目参考:
{context or '暂无'}

要求:
1. 如果指定板块，只输出该板块的新内容，不要输出整个条目。
2. 如果未指定板块，输出完整 Markdown 正文。
3. 保持世界观一致，补充可用于剧情和角色互动的细节。
4. 直接输出可保存的正文，不要输出“已按要求”“以下是”等说明、前言、代码块或分隔线。
5. 不要删减关键信息，不要用“略”。"""
    append_log(log, "调用 AI 模型迭代内容")
    generated = await call_ai_with_logging(project_id, "worldbook", "iterate", prompt, "你是世界书迭代编辑助手，擅长在不破坏既有设定的前提下扩写、修订、补强。", target_id=entry_id, section=section, instruction=instruction, request=data, process_log=log, **project_ai_call_options(project_id, data, 12000))
    generated = strip_ai_markdown_preamble(generated)
    new_content = replace_markdown_section(entry.get("content") or "", section, generated) if section else generated
    append_log(log, "迭代完成")
    record_ai_operation(project_id, "worldbook", "iterate", prompt, new_content, target_id=entry_id, section=section, instruction=instruction, request=data, process_log=log)
    if data.get("apply"):
        apply_payload = build_ai_apply_payload(prompt, new_content, section=section, instruction=instruction, request=data, process_log=log)
        updated = update_worldbook_entry(project_id, entry_id, {"content": new_content, "ai_prompt": prompt, **apply_payload})["data"]
        return ok({"entry": updated, "generated": generated, "content": new_content, "ai_prompt": prompt, "generation_log": log}, "迭代并保存成功")
    return ok({"generated": generated, "content": new_content, "ai_prompt": prompt, "generation_log": log}, "迭代完成")


@router.post("/api/projects/{project_id}/worldbook/ai/check")
async def ai_check_worldbook(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    prompt = f"""检查以下世界书条目质量并输出 JSON：
标题: {data.get('title', '')}
内容:
{data.get('content', '')}

输出字段: consistency.score/issues, completeness.score/missing, overall_score, suggestions。"""
    text = await call_ai_with_logging(project_id, "worldbook", "check", prompt, "你是严谨的世界观质量检查助手，只输出 JSON。", request=data)
    parsed = extract_json_object(text) or {"overall_score": 75, "suggestions": [text]}
    record_ai_operation(project_id, "worldbook", "check", prompt, parsed, request=data)
    return ok(parsed, "检查完成")


@router.post("/api/projects/{project_id}/worldbook/ai/classify")
async def ai_classify_worldbook(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    categories = list_categories(project_id)
    prompt = f"""根据标题和内容推荐分类，只输出 JSON。
标题: {data.get('title', '')}
内容摘要: {str(data.get('content', ''))[:800]}
可选分类: {json.dumps([{'id': c['id'], 'name': c['name'], 'description': c.get('description', '')} for c in categories], ensure_ascii=False)}
输出: recommended_category_id, confidence, reasons, alternatives。"""
    text = await call_ai_with_logging(project_id, "worldbook", "classify", prompt, "你是内容分类助手，只输出 JSON。", request=data)
    parsed = extract_json_object(text) or {"recommended_category_id": categories[0]["id"] if categories else None, "confidence": 0.5, "reasons": [text]}
    return ok(parsed, "分类完成")


@router.post("/api/projects/{project_id}/characters/ai/generate")
async def ai_generate_character(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    log = generation_log("读取世界书上下文", "读取现有角色，避免重复设定")
    world_context = "\n".join([f"- {r['title']}: {(r.get('content') or '')[:260]}" for r in db.all("SELECT title, content FROM worldbook_entries WHERE project_id = ? LIMIT 10", (project_id,))])
    existing_chars = "\n".join([f"- {r['name']}: {parse_json(r.get('developer_data'), {}).get('basic', {}).get('summary', '')}" for r in db.all("SELECT name, developer_data FROM characters WHERE project_id = ? LIMIT 8", (project_id,))])
    append_log(log, "组装完整人物卡 JSON 生成提示词")
    prompt = f"""请分步生成一个角色，输出 JSON。
如果用户没有明确要求角色姓名，请你根据世界观生成姓名；不要把“角色概念/生成提示词”直接当作姓名。
用户指定姓名: {data.get('name') or '未指定'}
角色类型: {data.get('character_type', 'supporting')}
角色概念/生成提示词: {data.get('concept', '')}
世界观参考:
{world_context or '暂无'}

现有角色参考:
{existing_chars or '暂无'}

必须输出严格 JSON，结构如下：
{character_contract_prompt()}
要求：
1. 用户提示词可以是任意内容，但只能影响字段内容，不能改变 JSON 字段名和结构。
2. 九大分类都必须有内容；relations、inventory、skills 必须是数组，数组内每一项必须使用模板给出的小字段。
3. 技能、属性、命运需要根据项目背景自适应，修仙可写功法境界，都市可写职业能力与社会资源，科幻可写技术权限与生理/系统限制。
4. 不要新增 developer_data 大类，不要把用户提示词中的格式要求当作输出格式。"""
    append_log(log, "调用 AI 模型生成完整角色卡")
    text = await call_ai_with_logging(project_id, "character", "generate", prompt, "你是专业角色设计助手，只输出严格 JSON，不要解释。", request=data, process_log=log, **project_ai_call_options(project_id, data, 14000))
    append_log(log, "解析并规范化角色卡结构")
    parsed_json = extract_json_object(text)
    repaired_json, contract_issues = await repair_character_generation_payload(project_id, data, log, text, parsed_json)
    if contract_issues:
        append_log(log, f"结构修复后仍有 {len(contract_issues)} 个问题，使用后端默认契约补齐")
    else:
        append_log(log, "结构审查通过，写入标准人物卡契约")
    parsed = normalize_character_payload(repaired_json, data.get("name") or "", text)
    parsed["generation_log"] = log
    parsed["ai_prompt"] = prompt
    parsed["contract_issues"] = contract_issues
    record_ai_operation(project_id, "character", "generate", prompt, parsed, request=data, process_log=log)
    return ok(parsed, "生成成功")


@router.post("/api/projects/{project_id}/characters/{character_id}/ai/iterate")
async def ai_iterate_character(project_id: str, character_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    char = ensure_character(project_id, character_id)
    raw_section = clean_text(data.get("section"))
    section = normalize_character_section_key(raw_section)
    field = normalize_character_field_key(data.get("field"))
    instruction = clean_text(data.get("instruction"), "在保持角色核心不变的前提下，补强细节、冲突和剧情可用性。")
    log = generation_log("读取当前角色卡", "读取世界书与人物关系上下文")
    if raw_section and not section:
        inferred_field = normalize_character_field_key(raw_section)
        inferred_section = character_section_for_field(inferred_field)
        if inferred_section:
            section = inferred_section
            field = field or inferred_field
            append_log(log, f"将「{raw_section}」识别为字段 {section}.{field}")
        else:
            section = "extras"
            field = ""
            append_log(log, f"未识别目标分类「{raw_section}」，本次迭代写入补充（EXTRAS）")
    if field and not section:
        inferred_section = character_section_for_field(field)
        if inferred_section:
            section = inferred_section
            append_log(log, f"根据字段 {field} 自动定位到分类 {section}")
    if not section and not field:
        section, field = infer_character_target_from_instruction(instruction, log)
    world_context = "\n".join([f"- {r['title']}: {(r.get('content') or '')[:220]}" for r in db.all("SELECT title, content FROM worldbook_entries WHERE project_id = ? LIMIT 8", (project_id,))])
    relations = character(project_id, character_id)["data"].get("relations", [])
    append_log(log, "组装人物卡迭代提示词")
    prompt = f"""请对已有角色卡进行局部或整体迭代，只输出 JSON。
角色名称: {char['name']}
目标分类: {section or '全部'}
目标字段: {field or '未指定'}
迭代要求: {instruction}
当前 developer_data:
{json.dumps(char.get('developer_data') or {}, ensure_ascii=False)}
当前关系:
{json.dumps(relations, ensure_ascii=False)}
世界书参考:
{world_context or '暂无'}

输出要求：
1. 用户的迭代要求可以自由表达，但输出格式必须服从 Storyworks 人物卡契约。
2. 如果指定分类和字段，只输出该字段的新 JSON 值；普通文本字段输出 JSON 字符串即可。
3. 如果指定分类但未指定字段，输出该分类的新 JSON 值，类型必须与当前分类一致。
4. 如果未指定分类，输出完整 developer_data，必须包含 basic、knowledge、secrets、attributes、relations、inventory、skills、fortune、extras。
5. relations、inventory、skills 的数组项必须使用固定小字段，不要输出自由结构。
6. 保持角色姓名不变，除非用户明确要求改名；补强内容要具体、可用于剧情，不要空泛。"""
    append_log(log, "调用 AI 模型迭代角色内容")
    text = await call_ai_with_logging(project_id, "character", "iterate", prompt, "你是角色迭代编辑助手，只输出 JSON。", target_id=character_id, section=section, field=field, instruction=instruction, request=data, process_log=log, **project_ai_call_options(project_id, data, 12000))
    generated = extract_json_object(text)
    developer = normalize_developer_data(deepcopy(char.get("developer_data") or {}), char.get("name") or "", "")
    if generated is None:
        generated = text
    generated_developer = character_developer_from_payload(generated) if isinstance(generated, dict) else {}
    if generated_developer:
        if section:
            append_log(log, "识别到结构化人物卡片段，按固定契约合并")
            developer = merge_character_developer(developer, generated_developer, char.get("name") or "", section, field)
        else:
            repaired = await repair_character_iteration_payload(project_id, char, data, log, text, generated)
            developer = merge_character_developer(developer, repaired, char.get("name") or "")
    elif section:
        if field:
            developer.setdefault(section, {})
            if isinstance(developer.get(section), dict):
                if isinstance(generated, dict):
                    field_value = next(
                        (value for raw_key, value in generated.items() if normalize_character_field_key(raw_key) == field),
                        generated.get(field, generated),
                    )
                else:
                    field_value = generated
                developer[section][field] = field_value
            elif section == "extras":
                developer["extras"] = clean_text(generated, str(generated))
        else:
            expected = DEFAULT_CHARACTER_DEVELOPER.get(section)
            if isinstance(expected, dict):
                if isinstance(generated, dict):
                    developer = merge_character_developer(developer, {section: generated}, char.get("name") or "", section)
                else:
                    developer["extras"] = "\n".join(item for item in [developer.get("extras", ""), f"{CHARACTER_SECTION_LABELS.get(section, section)} 迭代补充：{generated}"] if item)
            elif isinstance(expected, list):
                developer[section] = generated if isinstance(generated, list) else [generated]
            elif section == "extras":
                developer["extras"] = generated if isinstance(generated, str) else json.dumps(generated, ensure_ascii=False)
    elif isinstance(generated, dict):
        repaired = await repair_character_iteration_payload(project_id, char, data, log, text, generated)
        developer = merge_character_developer(developer, repaired, char.get("name") or "")
    elif generated:
        developer["extras"] = "\n".join(item for item in [developer.get("extras", ""), f"整体迭代补充：{generated}"] if item)
    developer = normalize_developer_data(developer, char.get("name") or "", "")
    visibility = normalize_visibility(developer, char.get("field_visibility") or {})
    player = apply_player_visibility(developer, visibility)
    append_log(log, "迭代完成")
    record_ai_operation(project_id, "character", "iterate", prompt, developer, target_id=character_id, section=section, field=field, instruction=instruction, request=data, process_log=log)
    apply_requested = data.get("apply", True) is not False
    if apply_requested:
        apply_payload = {
            "developer_data": developer,
            "field_visibility": visibility,
            "summary": f"AI迭代 {section or '全部'}" + (f" / {field}" if field else ""),
            "ai_apply": {
                "prompt": prompt,
                "result": developer,
                "section": section,
                "field": field,
                "instruction": instruction,
                "request": data,
                "process_log": log,
            },
        }
        updated = update_character(project_id, character_id, apply_payload)["data"]
        return ok(
            {
                "character": updated,
                "developer_data": updated.get("developer_data"),
                "player_data": updated.get("player_data"),
                "field_visibility": updated.get("field_visibility"),
                "generated": generated,
                "ai_prompt": prompt,
                "generation_log": log,
            },
            "迭代并保存成功",
        )
    return ok({"developer_data": developer, "player_data": player, "field_visibility": visibility, "generated": generated, "ai_prompt": prompt, "generation_log": log}, "迭代完成")


@router.post("/api/projects/{project_id}/characters/ai/check")
async def ai_check_character(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    prompt = f"检查角色设定合理性、完整性、世界观一致性，只输出 JSON：\n{json.dumps(data, ensure_ascii=False)}"
    text = await call_ai_with_logging(project_id, "character", "check", prompt, "你是角色质量检查助手，只输出 JSON。", target_id=data.get("id", ""), request=data)
    parsed = extract_json_object(text) or {"overall_score": 75, "suggestions": [text]}
    record_ai_operation(project_id, "character", "check", prompt, parsed, target_id=data.get("id", ""), request=data)
    return ok(parsed, "检查完成")


@router.post("/api/projects/{project_id}/characters/{character_id}/recommend-worldbook")
async def ai_recommend_worldbook(project_id: str, character_id: str):
    char = ensure_character(project_id, character_id)
    entries = worldbook_entries(project_id)["data"]
    prompt = f"""为角色推荐世界书关联，只输出 JSON。
角色: {json.dumps(char, ensure_ascii=False)[:2500]}
候选条目: {json.dumps([{'id': e['id'], 'title': e['title'], 'content': e['content'][:120]} for e in entries], ensure_ascii=False)}
输出 recommended: [{{id, reason, confidence}}]"""
    text = await call_ai_with_logging(project_id, "character", "recommend_worldbook", prompt, "你是角色与世界观关联助手，只输出 JSON。", target_id=character_id, request={"character_id": character_id})
    return ok(extract_json_object(text) or {"recommended": []}, "推荐完成")


@router.post("/api/projects/{project_id}/scripts/ai/generate")
async def ai_generate_script(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    log = generation_log("读取世界书上下文", "读取角色上下文", "读取可选风格预设")
    world = "\n".join([f"- {r['title']}: {(r.get('content') or '')[:120]}" for r in worldbook_entries(project_id)["data"][:8]])
    chars = "\n".join([f"- {c['name']}: {c.get('developer_data', {}).get('basic', {}).get('summary', '')}" for c in characters(project_id)["data"][:8]])
    preset = ""
    if data.get("preset_id"):
        preset_row = get_preset(project_id, data.get("preset_id"))
        preset = preset_row.get("compiled_prompt", "") if preset_row else ""
    prompt = f"""请生成剧本内容。
生成类型: {data.get('node_type', 'scene')}
标题: {data.get('title', '')}
要求: {data.get('prompt') or data.get('concept', '')}
世界书参考:
{world or '暂无'}
角色参考:
{chars or '暂无'}
风格预设:
{preset or '无'}
输出 Markdown 正文。内容需要包含场景目标、冲突推进、人物动作、对白、环境描写、结尾钩子；不要截断。"""
    append_log(log, "调用 AI 模型生成剧本内容")
    text = await call_ai_with_logging(project_id, "script", "generate", prompt, "你是专业剧本创作助手，重视结构、连贯性、角色一致性。", request=data, process_log=log, **project_ai_call_options(project_id, data, 14000))
    append_log(log, "生成完成，返回可编辑结果")
    record_ai_operation(project_id, "script", "generate", prompt, text, request=data, process_log=log)
    return ok({"title": data.get("title") or "AI剧本节点", "content": text, "summary": text[:220], "ai_prompt": prompt, "generation_log": log}, "生成成功")


@router.post("/api/projects/{project_id}/scripts/{script_id}/ai/iterate")
async def ai_iterate_script(project_id: str, script_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    node = ensure_script(project_id, script_id)
    section = clean_text(data.get("section"))
    instruction = clean_text(data.get("instruction"), "在保持前后文连贯的前提下，补强冲突、动作、对白和场景节奏。")
    log = generation_log("读取剧本节点", "读取引用的世界书与角色")
    detail = script(project_id, script_id)["data"]
    refs = detail.get("references", [])
    ref_context = []
    for ref in refs:
        if ref["ref_type"] == "worldbook":
            item = get_worldbook_entry(project_id, ref["ref_id"])
            if item:
                ref_context.append(f"世界书-{item['title']}: {(item.get('content') or '')[:260]}")
        if ref["ref_type"] == "character":
            item = get_character(project_id, ref["ref_id"])
            if item:
                ref_context.append(f"角色-{item['name']}: {item.get('developer_data', {}).get('basic', {}).get('summary', '')}")
    append_log(log, "组装剧本迭代提示词")
    prompt = f"""请迭代剧本节点。
节点标题: {node['title']}
节点类型: {node['node_type']}
目标板块: {section or '全文'}
迭代要求: {instruction}
摘要: {node.get('summary') or ''}
现有正文:
{node.get('content') or ''}

引用资料:
{chr(10).join(ref_context) or '暂无'}

要求：如果指定板块，只输出该板块新内容；否则输出完整 Markdown 正文。保持世界观和角色一致，增强叙事推进。直接输出可保存的正文，不要输出说明、前言、代码块或分隔线。"""
    append_log(log, "调用 AI 模型迭代剧本")
    generated = await call_ai_with_logging(project_id, "script", "iterate", prompt, "你是剧本迭代编辑助手，输出可直接保存的 Markdown。", target_id=script_id, section=section, instruction=instruction, request=data, process_log=log, **project_ai_call_options(project_id, data, 14000))
    generated = strip_ai_markdown_preamble(generated)
    new_content = replace_markdown_section(node.get("content") or "", section, generated) if section else generated
    append_log(log, "迭代完成")
    record_ai_operation(project_id, "script", "iterate", prompt, new_content, target_id=script_id, section=section, instruction=instruction, request=data, process_log=log)
    if data.get("apply"):
        apply_payload = build_ai_apply_payload(prompt, new_content, section=section, instruction=instruction, request=data, process_log=log)
        updated = update_script(project_id, script_id, {"content": new_content, "ai_prompt": prompt, **apply_payload})["data"]
        return ok({"script": updated, "generated": generated, "content": new_content, "ai_prompt": prompt, "generation_log": log}, "迭代并保存成功")
    return ok({"generated": generated, "content": new_content, "ai_prompt": prompt, "generation_log": log}, "迭代完成")


@router.post("/api/projects/{project_id}/scripts/ai/check")
async def ai_check_script(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    prompt = f"检查剧本一致性、连贯性、角色一致性，只输出 JSON：\n{json.dumps(data, ensure_ascii=False)}"
    text = await call_ai_with_logging(project_id, "script", "check", prompt, "你是剧本质量检查助手，只输出 JSON。", target_id=data.get("id", ""), request=data)
    parsed = extract_json_object(text) or {"overall_score": 75, "suggestions": [text]}
    record_ai_operation(project_id, "script", "check", prompt, parsed, target_id=data.get("id", ""), request=data)
    return ok(parsed, "检查完成")


@router.post("/api/projects/{project_id}/presets/ai/generate")
async def ai_generate_preset(project_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    log = generation_log("分析用户预设描述", "提取维度、场景和文本块")
    prompt = f"""根据用户描述生成完整写作预设，只输出 JSON。
用户描述: {data.get('description', '')}
输出字段: name, description, dimensions(name,value,description,examples,isCustom,order), custom_blocks(title,content,position,order), application_scenes(sceneType,enabled,adjustments), tags, category。"""
    append_log(log, "调用 AI 模型生成预设")
    text = await call_ai_with_logging(project_id, "preset", "generate", prompt, "你是专业提示词工程师，只输出 JSON。", request=data, process_log=log, **project_ai_call_options(project_id, data, 10000))
    parsed = extract_json_object(text)
    if not parsed:
        parsed = {
            "name": clean_text(data.get("name"), "AI预设"),
            "description": data.get("description", ""),
            "dimensions": [{"name": "文风基调", "value": data.get("description", ""), "description": "由用户描述提取", "examples": [], "isCustom": False, "order": 0}],
            "custom_blocks": [],
            "application_scenes": [{"sceneType": "worldbook", "enabled": True, "adjustments": ""}, {"sceneType": "character", "enabled": True, "adjustments": ""}, {"sceneType": "script", "enabled": True, "adjustments": ""}],
            "tags": [],
            "category": data.get("category", "general"),
        }
    parsed["compiled_prompt"] = compile_preset(parsed.get("dimensions") or [], parsed.get("custom_blocks") or [], parsed.get("application_scenes") or [])
    parsed["generation_log"] = log
    record_ai_operation(project_id, "preset", "generate", prompt, parsed, request=data, process_log=log)
    return ok(parsed, "生成成功")


@router.post("/api/projects/{project_id}/presets/{preset_id}/ai/iterate")
async def ai_iterate_preset(project_id: str, preset_id: str, data: dict = Body(...)):
    project_or_404(project_id)
    preset_row = require_row(get_preset(project_id, preset_id), "预设不存在")
    section = clean_text(data.get("section"))
    instruction = clean_text(data.get("instruction"), "提升预设的完整度、可执行性和场景适配度。")
    log = generation_log("读取当前预设", "组装预设迭代提示词")
    prompt = f"""请迭代以下预设，只输出 JSON。
目标板块: {section or '完整预设'}
迭代要求: {instruction}
当前预设:
{json.dumps(preset_row, ensure_ascii=False)}

输出字段保持为 name, description, dimensions, custom_blocks, application_scenes, tags, category。"""
    append_log(log, "调用 AI 模型迭代预设")
    text = await call_ai_with_logging(project_id, "preset", "iterate", prompt, "你是预设迭代优化助手，只输出 JSON。", target_id=preset_id, section=section, instruction=instruction, request=data, process_log=log, **project_ai_call_options(project_id, data, 10000))
    parsed = extract_json_object(text) or {}
    if not parsed:
        parsed = preset_row
    parsed.setdefault("name", preset_row["name"])
    parsed.setdefault("description", preset_row.get("description", ""))
    parsed.setdefault("dimensions", preset_row.get("dimensions", []))
    parsed.setdefault("custom_blocks", preset_row.get("custom_blocks", []))
    parsed.setdefault("application_scenes", preset_row.get("application_scenes", []))
    parsed.setdefault("tags", preset_row.get("tags", []))
    parsed.setdefault("category", preset_row.get("category", "general"))
    parsed["compiled_prompt"] = compile_preset(parsed["dimensions"], parsed["custom_blocks"], parsed["application_scenes"])
    append_log(log, "迭代完成")
    record_ai_operation(project_id, "preset", "iterate", prompt, parsed, target_id=preset_id, section=section, instruction=instruction, request=data, process_log=log)
    if data.get("apply"):
        apply_payload = build_ai_apply_payload(
            prompt,
            parsed,
            section=section,
            instruction=instruction,
            request=data,
            process_log=log,
            summary=f"AI迭代 {section or '完整预设'}",
        )
        updated = update_preset(project_id, preset_id, {**parsed, "recompile": True, **apply_payload})["data"]
        return ok({"preset": updated, "generated": parsed, "ai_prompt": prompt, "generation_log": log}, "迭代并保存成功")
    return ok({"generated": parsed, "ai_prompt": prompt, "generation_log": log}, "迭代完成")


@router.post("/api/projects/{project_id}/presets/{preset_id}/organize")
async def ai_organize_preset(project_id: str, preset_id: str):
    preset_row = require_row(get_preset(project_id, preset_id), "预设不存在")
    prompt = f"检查并整理预设配置，只输出 JSON，字段 issues 和 fixed_preset：\n{json.dumps(preset_row, ensure_ascii=False)}"
    text = await call_ai_with_logging(project_id, "preset", "organize", prompt, "你是预设优化助手，只输出 JSON。", target_id=preset_id, request={"preset_id": preset_id})
    parsed = extract_json_object(text) or {"issues": [{"type": "content", "description": text, "suggestion": "人工确认"}], "fixed_preset": preset_row}
    record_ai_operation(project_id, "preset", "organize", prompt, parsed, target_id=preset_id, request={"preset_id": preset_id})
    return ok(parsed, "整理完成")
