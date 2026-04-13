import json
from copy import deepcopy
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.character_repository import CharacterRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.character import (
    CharacterCreate,
    CharacterGenerateRequest,
    CharacterGenerateResponse,
    CharacterUpdate,
)
from app.services.character_template_service import CharacterTemplateService
from app.validators.character_validator import (
    validate_character_create,
    validate_character_payload,
    validate_character_update,
)


class CharacterService:
    def __init__(self, db: Session):
        self.repository = CharacterRepository(db)
        self.project_repository = ProjectRepository(db)
        self.template_service = CharacterTemplateService()

    def list_templates(self):
        return self.template_service.list_templates()

    def get_template(self, template_id: str):
        try:
            return self.template_service.get_template(template_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character template not found.") from exc

    def list_characters(self, project_id: int):
        self._ensure_project_exists(project_id)
        return self.repository.list_by_project(project_id)

    def get_character(self, character_id: int):
        character = self.repository.get_by_id(character_id)
        if character is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found.")
        return character

    def create_character(self, project_id: int, payload: CharacterCreate):
        self._ensure_project_exists(project_id)
        template = self.get_template(payload.template_id)
        validate_character_create(payload, template)
        name, summary = self._derive_identity(payload.developer_mode)
        return self.repository.create(project_id, template["name"], name, summary, payload)

    def update_character(self, character_id: int, payload: CharacterUpdate):
        character = self.get_character(character_id)
        template = self.get_template(character.template_id)
        validate_character_update(payload, template)

        developer_mode = payload.developer_mode if payload.developer_mode is not None else character.developer_mode
        player_mode = payload.player_mode if payload.player_mode is not None else character.player_mode
        validate_character_payload(developer_mode, player_mode, template)

        name, summary = self._derive_identity(developer_mode)
        return self.repository.update(character, name, summary, payload)

    def delete_character(self, character_id: int) -> None:
        character = self.get_character(character_id)
        self.repository.delete(character)

    def generate_draft(self, payload: CharacterGenerateRequest) -> CharacterGenerateResponse:
        template = self.get_template(payload.template_id)
        tabs = template["config"]["tabs"]
        fields = template["config"]["fields"]

        developer_mode = {tab["id"]: {} for tab in tabs}
        player_mode = {tab["id"]: {} for tab in tabs}

        name = self._derive_name(payload.name_hint, payload.concept)
        identity = self._derive_identity_text(payload.concept)
        tier = self._derive_tier(payload.project_context, payload.concept)
        summary = self._build_summary(name, identity, payload.concept)

        for field in fields:
            developer_value = self._generate_field_value(field, name, identity, tier, payload)
            self._set_nested_value(developer_mode, field["path"], developer_value)

            if field["tab"] in {"tab_secrets", "tab_fortune"}:
                player_value: Any = "未知"
            else:
                player_value = self._generate_player_value(field, developer_value, payload)
            self._set_nested_value(player_mode, field["path"], player_value)

        meta = {
            "generation_source": "rule_based_draft",
            "template_id": template["template_id"],
            "template_name": template["name"],
        }
        notes = "该人物卡草稿由模板驱动规则生成，建议创作者重点修订背景、关系、秘密信息与命运线索。"

        validate_character_payload(developer_mode, player_mode, template)

        return CharacterGenerateResponse(
            template_id=template["template_id"],
            template_name=template["name"],
            name=name,
            summary=summary,
            developer_mode=developer_mode,
            player_mode=player_mode,
            meta=meta,
            notes=notes,
            status=payload.status.strip() or "draft",
        )

    def export_character(self, character_id: int, export_format: str) -> dict[str, Any] | str:
        character = self.get_character(character_id)
        if export_format == "json":
            return {
                "id": character.id,
                "project_id": character.project_id,
                "template_id": character.template_id,
                "template_name": character.template_name,
                "name": character.name,
                "summary": character.summary,
                "developer_mode": character.developer_mode,
                "player_mode": character.player_mode,
                "meta": character.meta,
                "notes": character.notes,
                "status": character.status,
            }

        if export_format == "markdown":
            return self._to_markdown(character)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported export format. Use 'json' or 'markdown'.",
        )

    def _ensure_project_exists(self, project_id: int) -> None:
        if self.project_repository.get_by_id(project_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    @staticmethod
    def _set_nested_value(container: dict[str, Any], path: str, value: Any) -> None:
        current = container
        parts = path.split(".")
        for key in parts[:-1]:
            current = current.setdefault(key, {})
        current[parts[-1]] = value

    @staticmethod
    def _derive_identity(developer_mode: dict[str, Any]) -> tuple[str, str]:
        name = (
            developer_mode.get("tab_basic", {}).get("f_name")
            or developer_mode.get("tab_basic", {}).get("name")
            or "未命名角色"
        )
        summary = developer_mode.get("tab_basic", {}).get("f_desc") or ""
        return str(name).strip() or "未命名角色", str(summary).strip()

    @staticmethod
    def _derive_name(name_hint: str, concept: str) -> str:
        if name_hint.strip():
            return name_hint.strip()
        text = concept.replace("，", " ").replace(",", " ").strip()
        if not text:
            return "未命名角色"
        candidate = text.split()[0][:12].strip()
        return candidate or "未命名角色"

    @staticmethod
    def _derive_identity_text(concept: str) -> str:
        if concept.strip():
            return f"基于“{concept.strip()[:30]}”塑造的关键角色"
        return "待补充出身与职责的关键角色"

    @staticmethod
    def _derive_tier(project_context: str, concept: str) -> str:
        source = f"{project_context} {concept}".strip()
        if any(keyword in source for keyword in ["修士", "仙", "宗门", "法术"]):
            return "入门超凡层级"
        if any(keyword in source for keyword in ["军", "骑士", "战士", "佣兵"]):
            return "受训战斗层级"
        return "普通人层级"

    @staticmethod
    def _build_summary(name: str, identity: str, concept: str) -> str:
        if concept.strip():
            return f"{name}是{identity}，其人物核心围绕“{concept.strip()[:50]}”展开。"
        return f"{name}是{identity}，适合作为可继续扩写的人物草稿。"

    def _generate_field_value(
        self,
        field: dict[str, Any],
        name: str,
        identity: str,
        tier: str,
        payload: CharacterGenerateRequest,
    ) -> Any:
        field_id = field["id"]
        concept = payload.concept.strip()
        project_context = payload.project_context.strip()

        if field_id == "f_name":
            return name
        if field_id == "f_identity":
            return identity
        if field_id == "f_tier":
            return tier
        if field_id == "f_desc":
            return self._build_summary(name, identity, concept)
        if field_id == "f_personality":
            return f"{name}整体给人的感觉克制而清醒，面对压力时更倾向先观察再行动。其外在气质会因“{concept or identity}”而显得鲜明，适合塑造成有明确立场与弱点的人物。"
        if field_id == "f_appearance":
            return f"{name}在外貌上具有较高辨识度，衣着、神情与举止会体现其身份来源。建议进一步补充年龄感、体型、穿着习惯与标志性特征，使其更适合长期创作使用。"
        if field_id == "f_bg":
            return f"{name}的成长经历与当前身份密切相关，建议围绕“{concept or identity}”补充其出身、转折、当前处境与主要动机。若项目背景为“{project_context or '未指定'}”，应进一步写明其与该背景之间的连接。"
        if field_id == "f_trauma":
            return f"{name}心中保留着尚未对外公开的伤口，这段经历塑造了其谨慎、回避或执拗的一面。建议补充创伤来源、触发点与对关键关系的影响。"
        if field_id == "f_h_ident":
            return [
                {
                    "name": "未公开真实立场",
                    "detail": f"{name}表面身份与真实目标之间存在差异，建议结合“{concept or identity}”继续细化。",
                }
            ]
        if field_id == "f_core_stats":
            return {
                "strength": 5,
                "agility": 6,
                "constitution": 5,
                "intelligence": 7,
                "willpower": 7,
                "perception": 6,
                "summary": "整体均衡，智力与意志略突出。",
            }
        if field_id == "f_health":
            return {
                "physical": "基本健康",
                "mental": "保持警惕",
                "injuries": [],
                "status_effects": [],
                "energy": "中等",
                "stability": "可控",
            }
        if field_id == "f_rel_graph":
            return [
                {
                    "target": "玩家/主角",
                    "relation": "待建立",
                    "attitude": "谨慎观察",
                    "detail": f"{name}与主角之间的关系仍有较大塑造空间。",
                    "visibility": "public",
                }
            ]
        if field_id == "f_equip":
            return [
                {
                    "name": "常用随身装备",
                    "slot": "utility",
                    "quality": "普通",
                    "desc": f"与{name}的身份和出行方式相符，可继续细化。",
                }
            ]
        if field_id == "f_items":
            return [
                {
                    "name": "个人随身物",
                    "count": 1,
                    "type": "personal",
                    "desc": f"可体现{name}过往经历或当前任务的物品。",
                }
            ]
        if field_id == "f_skills":
            return [
                {
                    "name": "基础专长",
                    "type": "通用",
                    "level": "熟练",
                    "desc": f"与“{concept or identity}”相匹配的核心能力。",
                }
            ]
        if field_id == "f_destiny":
            return {
                "core": ["关键角色", "可持续扩写"],
                "latent": ["待揭示真实目标", "可能影响主线走向"],
            }
        if field_id == "f_fate_lines":
            return [
                {
                    "title": "身份揭示",
                    "trigger": "与主角建立稳定互动后",
                    "direction": "关系深化或冲突升级",
                    "detail": f"{name}隐藏信息被揭开后，会重新定义其在故事中的位置。",
                }
            ]

        return f"待补充：{field['label']}"

    @staticmethod
    def _generate_player_value(field: dict[str, Any], developer_value: Any, payload: CharacterGenerateRequest) -> Any:
        field_id = field["id"]
        if field_id in {"f_bg", "f_core_stats", "f_health", "f_h_ident", "f_destiny", "f_fate_lines"}:
            return "未知"

        if isinstance(developer_value, (dict, list)):
            return deepcopy(developer_value)
        return developer_value

    @staticmethod
    def _to_markdown(character: Any) -> str:
        lines = [
            f"# {character.name}",
            "",
            f"- 模板：{character.template_name}",
            f"- 状态：{character.status}",
            "",
            "## 简述",
            "",
            character.summary or "暂无简述。",
            "",
            "## Developer Mode",
            "",
            "```json",
            json.dumps(character.developer_mode, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Player Mode",
            "",
            "```json",
            json.dumps(character.player_mode, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Meta",
            "",
            "```json",
            json.dumps(character.meta, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Notes",
            "",
            character.notes or "暂无备注。",
            "",
        ]
        return "\n".join(lines)
