from __future__ import annotations

from copy import deepcopy
from typing import Any


CHARACTER_SECTIONS = ["basic", "knowledge", "secrets", "attributes", "relations", "inventory", "skills", "fortune", "extras"]

CHARACTER_SECTION_LABELS = {
    "basic": "基础（BASIC）",
    "knowledge": "信息（KNOWLEDGE）",
    "secrets": "隐秘（SECRETS）",
    "attributes": "属性（ATTRIBUTES）",
    "relations": "关系（RELATIONS）",
    "inventory": "物品（INVENTORY）",
    "skills": "技能（SKILLS）",
    "fortune": "命运（FORTUNE）",
    "extras": "补充（EXTRAS）",
}

CHARACTER_FIELD_LABELS = {
    "name": "姓名（name）",
    "gender": "性别（gender）",
    "age": "年龄（age）",
    "identity": "身份（identity）",
    "role": "叙事定位（role）",
    "status": "当前状态（status）",
    "summary": "摘要（summary）",
    "appearance": "外观特征（appearance）",
    "personality": "性格模式（personality）",
    "background": "背景经历（background）",
    "dailyLife": "日常处境（dailyLife）",
    "motivation": "行动动机（motivation）",
    "values": "价值观（values）",
    "flaws": "弱点缺陷（flaws）",
    "currentConflict": "当前冲突（currentConflict）",
    "publicMask": "公开面具（publicMask）",
    "privateTruth": "私下真相（privateTruth）",
    "trauma": "创伤（trauma）",
    "hiddenAgenda": "隐藏目标（hiddenAgenda）",
    "weakness": "软肋（weakness）",
    "revealTrigger": "揭露触发（revealTrigger）",
    "physical": "身体/外在能力（physical）",
    "mental": "心智/认知能力（mental）",
    "social": "社会影响力（social）",
    "resources": "资源筹码（resources）",
    "limitations": "限制代价（limitations）",
    "special": "特殊设定（special）",
    "targetName": "目标角色（targetName）",
    "relationType": "关系类型（relationType）",
    "direction": "方向（direction）",
    "intimacy": "亲近度（intimacy）",
    "conflict": "关系冲突（conflict）",
    "history": "关系历史（history）",
    "leverage": "牵制筹码（leverage）",
    "currentStatus": "当前关系状态（currentStatus）",
    "events": "事件记录（events）",
    "itemName": "物品名称（itemName）",
    "type": "类型（type）",
    "owner": "归属（owner）",
    "function": "用途（function）",
    "origin": "来源（origin）",
    "storyUse": "剧情用途（storyUse）",
    "category": "类别（category）",
    "level": "等级/熟练度（level）",
    "effect": "效果（effect）",
    "cost": "代价（cost）",
    "trainingSource": "来源训练（trainingSource）",
    "desire": "核心渴望（desire）",
    "fear": "核心恐惧（fear）",
    "destinyTags": "命运标签（destinyTags）",
    "turningPoints": "转折节点（turningPoints）",
    "choices": "关键选择（choices）",
    "causalHints": "因果钩子（causalHints）",
}

CHARACTER_FIELD_ALIASES = {
    "名字": "name",
    "姓名": "name",
    "性别": "gender",
    "年龄": "age",
    "身份": "identity",
    "职业": "identity",
    "定位": "role",
    "叙事定位": "role",
    "状态": "status",
    "等级": "status",
    "境界": "status",
    "修为": "status",
    "level": "status",
    "摘要": "summary",
    "简介": "summary",
    "概述": "summary",
    "介绍": "summary",
    "描述": "summary",
    "人物描述": "summary",
    "角色描述": "summary",
    "description": "summary",
    "desc": "summary",
    "bio": "summary",
    "profile": "summary",
    "外貌": "appearance",
    "外观": "appearance",
    "形象": "appearance",
    "外观特征": "appearance",
    "性格": "personality",
    "人格": "personality",
    "背景": "background",
    "经历": "background",
    "身世": "background",
    "背景经历": "background",
    "日常": "dailyLife",
    "日常生活": "dailyLife",
    "日常处境": "dailyLife",
    "动机": "motivation",
    "行动动机": "motivation",
    "目标": "motivation",
    "价值观": "values",
    "信念": "values",
    "缺点": "flaws",
    "缺陷": "flaws",
    "弱点缺陷": "flaws",
    "当前冲突": "currentConflict",
    "冲突": "currentConflict",
    "公开形象": "publicMask",
    "公开面具": "publicMask",
    "面具": "publicMask",
    "秘密": "privateTruth",
    "隐秘": "privateTruth",
    "私下真相": "privateTruth",
    "隐秘真相": "privateTruth",
    "secret": "privateTruth",
    "hiddenIdentity": "privateTruth",
    "隐藏身份": "privateTruth",
    "创伤": "trauma",
    "心理创伤": "trauma",
    "隐藏目标": "hiddenAgenda",
    "真实目标": "hiddenAgenda",
    "软肋": "weakness",
    "弱点": "weakness",
    "揭露触发": "revealTrigger",
    "触发条件": "revealTrigger",
    "身体": "physical",
    "体能": "physical",
    "身体能力": "physical",
    "外在能力": "physical",
    "心智": "mental",
    "认知": "mental",
    "精神": "mental",
    "心智能力": "mental",
    "社会": "social",
    "社交": "social",
    "社会影响力": "social",
    "资源": "resources",
    "筹码": "resources",
    "资源筹码": "resources",
    "限制": "limitations",
    "限制代价": "limitations",
    "代价": "limitations",
    "短板": "limitations",
    "健康": "limitations",
    "伤势": "limitations",
    "旧伤": "limitations",
    "health": "limitations",
    "特殊": "special",
    "特殊设定": "special",
    "核心渴望": "desire",
    "渴望": "desire",
    "欲望": "desire",
    "核心恐惧": "fear",
    "恐惧": "fear",
    "命运标签": "destinyTags",
    "转折节点": "turningPoints",
    "关键选择": "choices",
    "因果钩子": "causalHints",
}

CHARACTER_LIST_ITEM_SCHEMAS = {
    "relations": {
        "targetName": "",
        "relationType": "",
        "direction": "bidirectional",
        "intimacy": 0,
        "conflict": "",
        "history": "",
        "leverage": "",
        "currentStatus": "",
        "events": [],
    },
    "inventory": {
        "itemName": "",
        "type": "",
        "owner": "",
        "function": "",
        "origin": "",
        "limitations": "",
        "storyUse": "",
    },
    "skills": {
        "name": "",
        "category": "",
        "level": "",
        "effect": "",
        "cost": "",
        "limitations": "",
        "trainingSource": "",
        "storyUse": "",
    },
}

DEFAULT_CHARACTER_DEVELOPER = {
    "basic": {"name": "", "gender": "", "age": "", "identity": "", "role": "", "status": "", "summary": ""},
    "knowledge": {
        "appearance": "",
        "personality": "",
        "background": "",
        "dailyLife": "",
        "motivation": "",
        "values": "",
        "flaws": "",
        "currentConflict": "",
    },
    "secrets": {"publicMask": "", "privateTruth": "", "trauma": "", "hiddenAgenda": "", "weakness": "", "revealTrigger": ""},
    "attributes": {"physical": "", "mental": "", "social": "", "resources": "", "limitations": "", "special": ""},
    "relations": [],
    "inventory": [],
    "skills": [],
    "fortune": {"desire": "", "fear": "", "destinyTags": [], "turningPoints": [], "choices": [], "causalHints": []},
    "extras": "",
}

CHARACTER_DICT_FIELD_SECTIONS = {
    field: section
    for section, fields in DEFAULT_CHARACTER_DEVELOPER.items()
    if isinstance(fields, dict)
    for field in fields
}

SECTION_VISIBILITY_DEFAULTS = {
    "basic": True,
    "knowledge": True,
    "secrets": False,
    "attributes": True,
    "relations": True,
    "inventory": True,
    "skills": True,
    "fortune": False,
    "extras": True,
}


def character_section_label(key: str) -> str:
    return CHARACTER_SECTION_LABELS.get(key, f"补充分类（{key.upper()}）")


def character_field_label(key: str) -> str:
    return CHARACTER_FIELD_LABELS.get(key, f"补充字段（{key}）")


def normalize_character_field_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    for alias, field in CHARACTER_FIELD_ALIASES.items():
        if lowered == alias.lower():
            return field
    if text in CHARACTER_FIELD_LABELS:
        return text
    for key, label in CHARACTER_FIELD_LABELS.items():
        if lowered == key.lower() or text == label or text in label:
            return key
    return text


def character_section_for_field(field: str) -> str:
    return CHARACTER_DICT_FIELD_SECTIONS.get(normalize_character_field_name(field), "")


def default_character_data(name: str, concept: str = ""):
    developer = deepcopy(DEFAULT_CHARACTER_DEVELOPER)
    developer["basic"]["name"] = name
    developer["basic"]["summary"] = concept
    developer["knowledge"]["background"] = concept
    visibility = build_default_visibility(developer)
    player = apply_player_visibility(developer, visibility)
    return developer, player, visibility


def character_contract_template() -> dict:
    template = deepcopy(DEFAULT_CHARACTER_DEVELOPER)
    for section, schema in CHARACTER_LIST_ITEM_SCHEMAS.items():
        template[section] = [deepcopy(schema)]
    return template


def build_default_visibility(developer_data: dict) -> dict:
    visibility: dict[str, Any] = {}
    for section in CHARACTER_SECTIONS:
        value = developer_data.get(section, DEFAULT_CHARACTER_DEVELOPER.get(section))
        visible = SECTION_VISIBILITY_DEFAULTS.get(section, False)
        if isinstance(value, dict):
            visibility[section] = {
                key: {"visible": visible, "displayMode": "full" if visible else "hidden", "customDisplay": "" if visible else "未知"}
                for key in value
            }
        else:
            visibility[section] = {"__section__": {"visible": visible, "displayMode": "full" if visible else "hidden", "customDisplay": "" if visible else "未知"}}
    return visibility


def is_blank_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False


def normalize_list_section(section: str, incoming: Any) -> list:
    if is_blank_value(incoming):
        return []
    raw_items = incoming if isinstance(incoming, list) else [incoming]
    schema = CHARACTER_LIST_ITEM_SCHEMAS.get(section)
    if not schema:
        return raw_items

    normalized_items = []
    for item in raw_items:
        if is_blank_value(item):
            continue
        normalized_items.append(normalize_list_item(section, item, schema))
    return normalized_items


def normalize_list_item(section: str, item: Any, schema: dict) -> dict:
    normalized = deepcopy(schema)
    if isinstance(item, dict):
        for key in schema:
            if key in item and not is_blank_value(item[key]):
                normalized[key] = item[key]
        unknown = {key: value for key, value in item.items() if key not in schema and not is_blank_value(value)}
        if unknown:
            append_unknown_list_item_fields(section, normalized, unknown)
    else:
        append_unknown_list_item_fields(section, normalized, {"内容": item})

    if section == "relations":
        normalized["events"] = normalize_sequence(normalized.get("events"))
        try:
            normalized["intimacy"] = int(normalized.get("intimacy") or 0)
        except (TypeError, ValueError):
            normalized["intimacy"] = 0
    return normalized


def append_unknown_list_item_fields(section: str, target: dict, unknown: dict) -> None:
    text = stringify_extra(unknown)
    if section == "relations":
        target["history"] = append_extra(target.get("history", ""), text)
    else:
        target["storyUse"] = append_extra(target.get("storyUse", ""), text)


def normalize_sequence(value: Any) -> list:
    if is_blank_value(value):
        return []
    return value if isinstance(value, list) else [value]


def normalize_dict_section(section: str, incoming: dict, base: dict) -> None:
    section_fields = base.get(section)
    if not isinstance(section_fields, dict):
        return
    for raw_key, raw_value in incoming.items():
        field = normalize_character_field_name(raw_key)
        if field in section_fields:
            if not is_blank_value(raw_value) or raw_key == field:
                section_fields[field] = raw_value
            continue
        if not is_blank_value(raw_value):
            base["extras"] = append_extra(base.get("extras", ""), f"{character_section_label(section)} / {raw_key}：{stringify_extra(raw_value)}")


def normalize_developer_data(value: Any, name: str = "", concept: str = "") -> dict:
    base, _, _ = default_character_data(name, concept)
    if not isinstance(value, dict):
        return base

    for section in CHARACTER_SECTIONS:
        incoming = value.get(section)
        if incoming is None:
            continue
        if section in ("relations", "inventory", "skills"):
            base[section] = normalize_list_section(section, incoming)
        elif section == "extras":
            base[section] = append_extra(base.get(section, ""), incoming if isinstance(incoming, str) else stringify_extra(incoming))
        elif isinstance(base[section], dict):
            if isinstance(incoming, dict):
                normalize_dict_section(section, incoming, base)
            elif incoming:
                base["extras"] = append_extra(base["extras"], f"{character_section_label(section)}：{incoming}")
    if name:
        base["basic"]["name"] = base["basic"].get("name") or name
    base["basic"].setdefault("gender", "")
    return base


def normalize_visibility(developer_data: dict, visibility: Any) -> dict:
    base = build_default_visibility(developer_data)
    if not isinstance(visibility, dict):
        return base
    for section, rules in visibility.items():
        if section not in base or not isinstance(rules, dict):
            continue
        if "__section__" in base[section]:
            base[section]["__section__"].update(rules.get("__section__", rules))
        else:
            for field, rule in rules.items():
                if field in base[section] and isinstance(rule, dict):
                    base[section][field].update(rule)
    return base


def normalize_character_contract(row: dict | None) -> dict | None:
    if not row:
        return row
    developer = normalize_developer_data(row.get("developer_data") or {}, row.get("name") or "", "")
    row["developer_data"] = developer
    visibility = normalize_visibility(developer, row.get("field_visibility") or {})
    row["field_visibility"] = visibility
    player = row.get("player_data")
    if not isinstance(player, dict):
        row["player_data"] = apply_player_visibility(developer, visibility)
    else:
        row["player_data"] = normalize_player_data(player, developer, visibility)
    return row


def normalize_player_data(player: dict, developer: dict, visibility: dict) -> dict:
    normalized = apply_player_visibility(developer, visibility)
    for section in ("basic", "knowledge"):
        if isinstance(player.get(section), dict):
            normalized[section].update(player[section])
    return normalized


def apply_player_visibility(developer_data: dict, visibility: dict):
    player: dict[str, Any] = {}
    for section in CHARACTER_SECTIONS:
        value = developer_data.get(section)
        rules = visibility.get(section, {})
        if isinstance(value, dict):
            visible_fields = {}
            for field, field_value in value.items():
                rule = rules.get(field, {"visible": SECTION_VISIBILITY_DEFAULTS.get(section, False), "displayMode": "full", "customDisplay": ""})
                visible_fields[field] = visible_value(field_value, rule)
            if visible_fields:
                player[section] = visible_fields
        else:
            rule = rules.get("__section__", {"visible": SECTION_VISIBILITY_DEFAULTS.get(section, False), "displayMode": "full", "customDisplay": ""})
            rendered = visible_value(value, rule)
            if rendered not in (None, "", [], {}):
                player[section] = rendered
    return player


def visible_value(value: Any, rule: dict) -> Any:
    if rule.get("visible") and rule.get("displayMode") == "full":
        return value
    if rule.get("visible") and rule.get("displayMode") in ("partial", "custom"):
        return rule.get("customDisplay") or "部分可见"
    return rule.get("customDisplay") or "未知"


def append_extra(current: str, text: str) -> str:
    return "\n".join(item for item in [current, text] if item)


def stringify_extra(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
