import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.script_repository import ScriptRepository
from app.schemas.script import (
    ScriptCreate,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptUpdate,
)
from app.validators.script_validator import validate_script_create, validate_script_update


class ScriptService:
    def __init__(self, db: Session):
        self.repository = ScriptRepository(db)
        self.project_repository = ProjectRepository(db)

    def list_scripts(self, project_id: int):
        self._ensure_project_exists(project_id)
        return self.repository.list_by_project(project_id)

    def get_script(self, script_id: int):
        script = self.repository.get_by_id(script_id)
        if script is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found.")
        return script

    def create_script(self, project_id: int, payload: ScriptCreate):
        self._ensure_project_exists(project_id)
        validate_script_create(payload)
        return self.repository.create(project_id, payload)

    def update_script(self, script_id: int, payload: ScriptUpdate):
        validate_script_update(payload)
        script = self.get_script(script_id)
        return self.repository.update(script, payload)

    def delete_script(self, script_id: int) -> None:
        script = self.get_script(script_id)
        self.repository.delete(script)

    def generate_draft(self, payload: ScriptGenerateRequest) -> ScriptGenerateResponse:
        concept = payload.concept.strip()
        title = payload.title.strip()
        script_type = payload.script_type.strip() or "主线"
        theme = self._derive_theme(concept, payload.project_context)
        summary = self._build_summary(title, concept)
        main_characters = self._build_main_characters(concept)
        core_conflict = self._build_core_conflict(concept)
        story_stage = "开端：建立局势与主要冲突"
        major_nodes = self._build_major_nodes(title, concept)
        branch_ideas = self._build_branch_ideas()
        forbidden_content = "禁止让关键秘密在开局阶段被无铺垫揭露；禁止主线冲突在前期直接被解决。"
        chapters = self._build_chapters(title, concept)
        scene_cards = self._build_scene_cards(title)
        constraints = {
            "hard_constraints": [
                "主角必须在早期接触核心冲突。",
                "第一批场景必须建立世界规则和人物关系。",
            ],
            "soft_constraints": [
                "节奏以建立悬念和动机为主。",
                "每个场景都应推动信息、关系或目标中的至少一项。",
            ],
            "reveal_rules": [
                "秘密信息优先分阶段揭示。",
                "剧本中的重大真相不应在第一场景完全公开。",
            ],
        }
        notes = "该剧本草稿由规则化结构生成，建议创作者重点补充章节细节、角色动机与场景事件。"

        return ScriptGenerateResponse(
            title=title,
            script_type=script_type,
            theme=theme,
            summary=summary,
            main_characters=main_characters,
            core_conflict=core_conflict,
            story_stage=story_stage,
            major_nodes=major_nodes,
            branch_ideas=branch_ideas,
            forbidden_content=forbidden_content,
            chapters=chapters,
            scene_cards=scene_cards,
            constraints=constraints,
            notes=notes,
            status=payload.status.strip() or "draft",
        )

    def export_script(self, script_id: int, export_format: str) -> dict[str, Any] | str:
        script = self.get_script(script_id)
        if export_format == "json":
            return {
                "id": script.id,
                "project_id": script.project_id,
                "title": script.title,
                "script_type": script.script_type,
                "theme": script.theme,
                "summary": script.summary,
                "main_characters": script.main_characters,
                "core_conflict": script.core_conflict,
                "story_stage": script.story_stage,
                "major_nodes": script.major_nodes,
                "branch_ideas": script.branch_ideas,
                "forbidden_content": script.forbidden_content,
                "chapters": script.chapters,
                "scene_cards": script.scene_cards,
                "constraints": script.constraints,
                "notes": script.notes,
                "status": script.status,
            }

        if export_format == "markdown":
            return self._to_markdown(script)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported export format. Use 'json' or 'markdown'.",
        )

    def _ensure_project_exists(self, project_id: int) -> None:
        if self.project_repository.get_by_id(project_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    @staticmethod
    def _derive_theme(concept: str, project_context: str) -> str:
        source = f"{concept} {project_context}".strip()
        if "权力" in source or "政治" in source:
            return "权力、秩序与真相"
        if "成长" in source:
            return "成长与选择"
        if "复仇" in source:
            return "复仇与代价"
        return "秘密、冲突与命运"

    @staticmethod
    def _build_summary(title: str, concept: str) -> str:
        if concept:
            return f"《{title}》围绕“{concept[:80]}”展开，剧本重点在于建立主线目标、关键冲突和信息揭示顺序。"
        return f"《{title}》是一份待继续补充的结构化剧本草稿，用于约束后续剧情推进。"

    @staticmethod
    def _build_main_characters(concept: str) -> list[dict[str, Any] | str]:
        return [
            {"name": "主角", "role": "剧情推动者", "note": "负责进入冲突并承担主要选择。"},
            {"name": "关键对手", "role": "冲突制造者", "note": f"建议根据“{concept or '核心设定'}”继续细化。"},
        ]

    @staticmethod
    def _build_core_conflict(concept: str) -> str:
        if concept:
            return f"故事的核心冲突围绕“{concept[:120]}”展开，主角需要在风险与目标之间不断做出取舍。"
        return "主角所追求的目标与阻碍其前进的力量之间存在持续冲突。"

    @staticmethod
    def _build_major_nodes(title: str, concept: str) -> list[dict[str, Any] | str]:
        return [
            {"title": "引子", "detail": f"建立《{title}》的背景、人物位置和第一推动事件。"},
            {"title": "第一次转折", "detail": f"让主角正式卷入“{concept or '核心冲突'}”。"},
            {"title": "中段升级", "detail": "冲突扩大，支线与秘密开始影响主线判断。"},
            {"title": "高潮前夜", "detail": "关键关系重组，真相接近揭露。"},
        ]

    @staticmethod
    def _build_branch_ideas() -> list[dict[str, Any] | str]:
        return [
            {"title": "关系分支", "detail": "根据主角与关键角色的信任变化开启不同走向。"},
            {"title": "情报分支", "detail": "根据掌握信息量决定场景可揭示内容。"},
        ]

    @staticmethod
    def _build_chapters(title: str, concept: str) -> list[dict[str, Any]]:
        return [
            {
                "title": f"{title}·第一章",
                "goal": "建立背景与事件入口",
                "summary": f"围绕“{concept or '主要冲突'}”展开开篇铺垫，建立主角与问题之间的连接。",
            },
            {
                "title": f"{title}·第二章",
                "goal": "推动冲突升级",
                "summary": "让人物关系、线索与风险同步上升，为后续故事弧建立动力。",
            },
        ]

    @staticmethod
    def _build_scene_cards(title: str) -> list[dict[str, Any]]:
        return [
            {
                "title": f"{title}·场景一",
                "goal": "建立主角处境",
                "location": "开篇关键地点",
                "participants": ["主角", "关键配角"],
                "entry_conditions": ["故事开始", "角色首次登场"],
                "conflict": "角色目标与现实阻力第一次发生碰撞",
                "must_happen": ["主角获得推动剧情的第一线索"],
                "optional_events": ["与配角形成初步关系"],
                "forbidden_events": ["终局真相被完全公开"],
                "exit_conditions": ["主角决定继续追查或行动"],
                "reveal_info": ["世界规则的基础信息", "关键问题的存在"],
            },
            {
                "title": f"{title}·场景二",
                "goal": "扩大风险",
                "location": "次级冲突地点",
                "participants": ["主角", "对立人物"],
                "entry_conditions": ["第一线索已触发"],
                "conflict": "主角与反对力量直接接触",
                "must_happen": ["冲突升级并带来代价"],
                "optional_events": ["揭示新的关系线索"],
                "forbidden_events": ["主线危机提前解决"],
                "exit_conditions": ["主角进入下一阶段选择"],
                "reveal_info": ["更具体的敌意或阻碍来源"],
            },
        ]

    @staticmethod
    def _to_markdown(script: Any) -> str:
        lines = [
            f"# {script.title}",
            "",
            f"- 类型：{script.script_type}",
            f"- 状态：{script.status}",
            f"- 主题：{script.theme or '未设置'}",
            "",
            "## 故事摘要",
            "",
            script.summary or "暂无摘要。",
            "",
            "## 主要人物",
            "",
            "```json",
            json.dumps(script.main_characters, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 核心冲突",
            "",
            script.core_conflict or "暂无内容。",
            "",
            "## 故事阶段",
            "",
            script.story_stage or "暂无内容。",
            "",
            "## 主要节点",
            "",
            "```json",
            json.dumps(script.major_nodes, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 分支设想",
            "",
            "```json",
            json.dumps(script.branch_ideas, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 章节结构",
            "",
            "```json",
            json.dumps(script.chapters, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 场景卡",
            "",
            "```json",
            json.dumps(script.scene_cards, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 剧情约束",
            "",
            "```json",
            json.dumps(script.constraints, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 禁止越界内容",
            "",
            script.forbidden_content or "暂无内容。",
            "",
            "## Notes",
            "",
            script.notes or "暂无备注。",
            "",
        ]
        return "\n".join(lines)
