from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from shared.config import config

from ..database import db, new_id, now, to_json, to_json_array


def clean_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip()


def extract_json_object(text: str) -> Optional[dict]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except Exception:
            pass

    start_positions = [idx for idx, char in enumerate(text) if char == "{"]
    for start in start_positions:
        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(text)):
            char = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : idx + 1])
                    except Exception:
                        break
    return None


AI_MARKDOWN_PREAMBLE_HINTS = (
    "已按要求",
    "以下是",
    "下面是",
    "为你",
    "Here is",
    "I've",
    "I have",
)


def strip_ai_markdown_preamble(text: str) -> str:
    """Remove model narration before a real Markdown document when it is clearly present."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    fenced = re.fullmatch(r"```(?:markdown|md)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    heading = re.search(r"(?m)^#{1,3}\s+\S", cleaned)
    if not heading or heading.start() == 0:
        return cleaned

    prefix = cleaned[: heading.start()].strip()
    if not prefix:
        return cleaned[heading.start() :].strip()
    normalized_prefix = prefix.replace("-", "").replace("*", "").strip()
    if any(hint.lower() in normalized_prefix.lower() for hint in AI_MARKDOWN_PREAMBLE_HINTS):
        return cleaned[heading.start() :].strip()
    return cleaned


def mock_ai_response(prompt: str, system_prompt: str = "") -> str:
    combined = f"{system_prompt}\n{prompt}"
    if "内容分类助手" in combined:
        category_ids = re.findall(r'"id":\s*"([^"]+)"', prompt)
        return json.dumps({"recommended_category_id": category_ids[0] if category_ids else None, "confidence": 0.82, "reasons": ["mock 模式根据候选分类返回首个可用分类"], "alternatives": category_ids[1:3]}, ensure_ascii=False)
    if "角色与世界观关联助手" in combined:
        entry_ids = [item for item in re.findall(r'"id":\s*"([^"]+)"', prompt) if item.startswith("world_")]
        return json.dumps({"recommended": [{"id": entry_ids[0], "reason": "mock 模式选择第一个世界书候选用于关联验证", "confidence": 0.8}] if entry_ids else []}, ensure_ascii=False)
    if "质量检查" in combined or "检查" in combined and "只输出 JSON" in combined and "预设" not in combined:
        return json.dumps({"overall_score": 88, "suggestions": ["mock 模式：结构完整，建议继续补充可执行细节。"], "consistency": {"score": 86, "issues": []}, "completeness": {"score": 88, "missing": []}}, ensure_ascii=False)
    if "角色设计助手" in combined or "完整角色卡" in combined or "人物卡结构化修复器" in combined or "人物卡迭代结构化修复器" in combined:
        name_match = re.search(r"用户指定姓名:\s*(.+)", prompt)
        raw_name = clean_text(name_match.group(1) if name_match else "", "")
        name = "" if raw_name in ("未指定", "None") else raw_name
        name = name or "云舟"
        return json.dumps(
            {
                "character_type": "supporting",
                "developer_data": {
                    "basic": {"name": name, "gender": "未定", "age": "青年", "identity": "mock 模式生成的试验角色", "role": "线索型同伴", "status": "调查中", "summary": "用于离线验证 AI 人物卡生成流程的角色，具备完整结构和后续剧情钩子。"},
                    "knowledge": {"appearance": "青衣木簪，随身携带旧罗盘", "personality": "谨慎、好奇、重承诺", "background": "曾在边境灵灾中协助迁民，因而接触到天阙封印异常。", "dailyLife": "在商路和宗门边境之间奔走，靠记录异常地脉换取资源。", "motivation": "寻找灵灾源头，同时保护仍在迁徙的凡人。", "values": "相信弱者也应拥有知道真相的权利。", "flaws": "过度承担责任，难以向他人求助。", "currentConflict": "需要在公开线索和保护幸存者之间做选择。"},
                    "secrets": {"publicMask": "只是普通阵法记录员", "privateTruth": "持有一枚未公开的阵钥碎片", "trauma": "曾因判断失误失去同伴", "hiddenAgenda": "确认阵钥碎片是否会引发新的灵灾", "weakness": "无法拒绝灵灾幸存者的请求", "revealTrigger": "阵钥碎片会在封印裂隙附近低鸣"},
                    "attributes": {"physical": "体能普通但耐力稳定", "mental": "擅长从异常细节中归纳规律", "social": "能在散修、商会和低阶弟子之间取得信任", "resources": "掌握边境灵灾记录和旧罗盘", "limitations": "灵脉轻微受损，过度感知会头痛", "special": "可短暂感知地脉逆流"},
                    "relations": [{"targetName": "林远", "relationType": "ally", "direction": "bidirectional", "intimacy": 35, "conflict": "是否公开封印裂隙线索", "history": "因剑骨预警与罗盘异动产生合作", "leverage": "阵钥碎片线索", "currentStatus": "谨慎合作", "events": []}],
                    "inventory": [{"itemName": "旧罗盘", "type": "法器/工具", "owner": name, "function": "指向封印裂隙", "origin": "灵灾遗物", "limitations": "每次使用都会留下裂纹", "storyUse": "推动角色进入异常地点"}],
                    "skills": [{"name": "地脉听息", "category": "感知/调查", "level": "入门", "effect": "感知地下灵流变化", "cost": "消耗精神并引发头痛", "limitations": "对人为伪装的阵法不稳定", "trainingSource": "灾后自学与旧罗盘反馈", "storyUse": "适合侦查和伏笔铺设"}],
                    "fortune": {"desire": "阻止下一场灵灾", "fear": "自己持有的碎片正是灾厄源头", "destinyTags": ["阵钥碎片", "灵灾幸存者"], "turningPoints": ["公开阵钥真相", "选择是否牺牲碎片救人"], "choices": ["保护个人秘密", "交给宗门审判", "与主角共同追查"], "causalHints": ["未来会在保护凡人与封印真相之间做选择"]},
                    "extras": "可作为任意背景下的调查型角色模板：在都市中可替换为事故调查员，在科幻中可替换为异常信号分析员。",
                },
                "field_visibility": {},
                "tags": ["mock", "AI"],
            },
            ensure_ascii=False,
        )
    if "角色迭代编辑助手" in combined:
        field_match = re.search(r"目标字段:\s*(.+)", prompt)
        field = clean_text(field_match.group(1) if field_match else "")
        if field and field != "未指定":
            return json.dumps({field: f"mock 模式迭代后的{field}内容，保留角色核心并补强剧情可用性。"}, ensure_ascii=False)
        return json.dumps({"summary": "mock 模式迭代后的角色摘要，补充了冲突、动机和后续剧情接口。"}, ensure_ascii=False)
    if "预设" in combined and "只输出 JSON" in combined:
        parsed = {
            "name": "mock 写作预设",
            "description": "用于离线验证预设生成与迭代的结构化结果。",
            "dimensions": [{"name": "文风基调", "value": "稳健细致", "description": "保持设定一致并给出可执行细节", "examples": ["规则、代价、剧情钩子同时出现"], "isCustom": False, "order": 0}],
            "custom_blocks": [{"title": "mock 执行规则", "content": "优先输出可直接进入正文或设定库的内容。", "position": "before", "order": 0}],
            "application_scenes": [{"sceneType": "worldbook", "enabled": True, "adjustments": "强调规则和冲突"}, {"sceneType": "character", "enabled": True, "adjustments": "强调动机和秘密"}, {"sceneType": "script", "enabled": True, "adjustments": "强调动作和对白"}],
            "tags": ["mock"],
            "category": "mock",
        }
        if "issues 和 fixed_preset" in combined:
            return json.dumps({"issues": [], "fixed_preset": parsed}, ensure_ascii=False)
        return json.dumps(parsed, ensure_ascii=False)
    if "世界观设定助手" in combined or "世界书迭代编辑助手" in combined or "请生成一个世界书条目" in combined:
        return "## 定义\nmock 模式生成的世界书内容，用于离线验证 AI 流程。\n\n## 规则\n该内容包含结构化标题、规则、冲突和剧情钩子。\n\n## 冲突\n条目与角色目标、阵营选择和后续场景发生稳定关联。\n\n## 钩子\n后续可以被角色和剧本引用。"
    if "剧本" in combined:
        return "## 场景目标\nmock 模式生成的剧本段落，用于验证 Markdown、版本和 AI 日志流程。\n\n## 冲突推进\n角色在有限信息下做出选择，留下后续反转钩子。\n\n## 结尾钩子\n罗盘裂纹指向新的封印裂隙。"
    return "## 定义\nmock 模式生成的世界书内容，用于离线验证 AI 流程。\n\n## 规则\n该内容包含结构化标题、规则、冲突和剧情钩子。\n\n## 钩子\n后续可以被角色和剧本引用。"


async def call_ai(
    prompt: str,
    system_prompt: str = "",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    process_log: Optional[list[dict]] = None,
) -> str:
    ai_config = config.ai_config
    if str(ai_config.get("provider", "")).lower() == "mock":
        return mock_ai_response(prompt, system_prompt)
    api_key = ai_config.get("apiKey")
    if not api_key:
        raise HTTPException(status_code=400, detail="未配置 AI API Key")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": ai_config.get("model", "gpt-4.1-mini"),
        "messages": messages,
        "temperature": temperature if temperature is not None else ai_config.get("temperature", 0.7),
        "max_tokens": max_tokens or max(ai_config.get("max_tokens", 4096), 8192),
    }
    continuation_limit = normalize_continuation_limit(ai_config.get("continuation_max", 2))
    url = chat_completions_url(ai_config.get("baseUrl", ""))
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    chunks: list[str] = []
    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(continuation_limit + 1):
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            choice = first_choice(data)
            chunk = choice_content(choice)
            if chunk:
                chunks.append(chunk)
            if not is_length_limited(choice):
                break
            if attempt >= continuation_limit:
                append_log(process_log, "模型输出仍可能被截断：已达到自动续写次数上限")
                break
            append_log(process_log, f"检测到模型输出被截断，自动续写第 {attempt + 1} 次")
            messages.append({"role": "assistant", "content": chunk})
            messages.append(
                {
                    "role": "user",
                    "content": "请从上一条回复的中断处继续输出。不要重复已经输出的内容，不要添加解释或新的前言，保持原本格式。",
                }
            )
            payload = {**payload, "messages": messages}
    return "".join(chunks)


def normalize_continuation_limit(value: Any) -> int:
    try:
        return max(0, min(int(value), 4))
    except (TypeError, ValueError):
        return 2


def first_choice(data: dict) -> dict:
    choices = data.get("choices") if isinstance(data, dict) else None
    if isinstance(choices, list) and choices:
        return choices[0] if isinstance(choices[0], dict) else {}
    return {}


def choice_content(choice: dict) -> str:
    message = choice.get("message") if isinstance(choice, dict) else None
    if isinstance(message, dict):
        return str(message.get("content") or "")
    return str(choice.get("text") or "")


def is_length_limited(choice: dict) -> bool:
    reason = str(choice.get("finish_reason") or choice.get("stop_reason") or "").lower()
    return reason in {"length", "max_tokens"}


def chat_completions_url(base_url: str) -> str:
    cleaned = str(base_url or "").rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    return f"{cleaned}/chat/completions"


def ai_error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    return str(exc) or exc.__class__.__name__


async def call_ai_with_logging(
    project_id: str,
    target_type: str,
    operation: str,
    prompt: str,
    system_prompt: str = "",
    *,
    target_id: str = "",
    section: str = "",
    field: str = "",
    instruction: str = "",
    request: Optional[dict] = None,
    process_log: Optional[list[dict]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    try:
        return await call_ai(prompt, system_prompt, temperature, max_tokens, process_log=process_log)
    except Exception as exc:
        message = ai_error_message(exc)
        failure_log = list(process_log or [])
        append_log(failure_log, f"AI 调用失败：{message}")
        record_ai_operation(
            project_id,
            target_type,
            operation,
            prompt,
            {"error": message},
            target_id=target_id,
            status="failed",
            section=section,
            field=field,
            instruction=instruction,
            request=request,
            process_log=failure_log,
        )
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=502, detail=f"AI 调用失败：{message}") from exc


def generation_log(*steps: str) -> list[dict]:
    return [{"time": now(), "message": step} for step in steps]


def append_log(log: list[dict], message: str):
    log.append({"time": now(), "message": message})


def preview_text(value: Any, limit: int = 1600) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value or "")
    return text[:limit]


def record_ai_operation(
    project_id: str,
    target_type: str,
    operation: str,
    prompt: str,
    result: Any,
    *,
    target_id: str = "",
    status: str = "success",
    section: str = "",
    field: str = "",
    instruction: str = "",
    request: Optional[dict] = None,
    process_log: Optional[list[dict]] = None,
):
    db.exec(
        """INSERT INTO ai_operation_logs
           (id, project_id, target_type, target_id, operation, status, section, field, instruction, prompt, request, response_preview, response_data, process_log, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            new_id("ailog"),
            project_id,
            target_type,
            target_id,
            operation,
            status,
            section,
            field,
            instruction,
            prompt,
            to_json(request or {}),
            preview_text(result),
            to_json(result),
            to_json_array(process_log or []),
            now(),
        ),
    )


def extract_markdown_section_text(content: str, section: str) -> str:
    if not section:
        return (content or "").strip()
    marker = f"## {section}"
    lines = (content or "").splitlines()
    start = -1
    for idx, line in enumerate(lines):
        if line.strip() == marker:
            start = idx
            break
    if start == -1:
        return (content or "").strip()
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(lines[start + 1 : end]).strip()


def replace_markdown_section(content: str, section: str, new_text: str) -> str:
    if not section:
        return new_text
    new_text = extract_markdown_section_text(new_text, section)
    marker = f"## {section}"
    lines = (content or "").splitlines()
    start = -1
    for idx, line in enumerate(lines):
        if line.strip() == marker:
            start = idx
            break
    replacement = [marker, "", new_text.strip()]
    if start == -1:
        base = content.rstrip()
        return f"{base}\n\n{marker}\n\n{new_text.strip()}".strip()
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(lines[:start] + replacement + lines[end:]).strip()
