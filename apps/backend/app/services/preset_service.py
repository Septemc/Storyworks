import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.preset_repository import PresetRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.preset import (
    PresetCreate,
    PresetGenerateRequest,
    PresetGenerateResponse,
    PresetTestRequest,
    PresetTestResponse,
    PresetUpdate,
)
from app.validators.preset_validator import (
    validate_preset_create,
    validate_preset_test,
    validate_preset_update,
)


class PresetService:
    def __init__(self, db: Session):
        self.repository = PresetRepository(db)
        self.project_repository = ProjectRepository(db)

    def list_presets(self, project_id: int):
        self._ensure_project_exists(project_id)
        return self.repository.list_by_project(project_id)

    def get_preset(self, preset_id: int):
        preset = self.repository.get_by_id(preset_id)
        if preset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found.")
        return preset

    def create_preset(self, project_id: int, payload: PresetCreate):
        self._ensure_project_exists(project_id)
        validate_preset_create(payload)
        return self.repository.create(project_id, payload)

    def update_preset(self, preset_id: int, payload: PresetUpdate):
        validate_preset_update(payload)
        preset = self.get_preset(preset_id)
        return self.repository.update(preset, payload)

    def delete_preset(self, preset_id: int) -> None:
        preset = self.get_preset(preset_id)
        self.repository.delete(preset)

    def generate_draft(self, payload: PresetGenerateRequest) -> PresetGenerateResponse:
        style_goal = payload.style_goal.strip()
        reference_text = payload.reference_text.strip()
        target_use = payload.target_use.strip()

        scope = target_use or "通用"
        style_description = self._build_style_description(style_goal, reference_text)
        wording_tendency = self._build_wording(style_goal)
        sentence_tendency = self._build_sentence(style_goal)
        description_density = self._build_description_density(style_goal)
        dialogue_ratio = self._build_dialogue_ratio(style_goal)
        rhythm_tendency = self._build_rhythm(style_goal)
        emotion_intensity = self._build_emotion(style_goal)
        plot_preferences = self._build_plot_preferences(style_goal)
        character_preferences = self._build_character_preferences(style_goal)
        forbidden_expressions = ["空泛形容词堆叠", "无节制重复", "无依据的突然转调"]
        output_requirements = [
            "表达应保持风格一致",
            "重要描写应具体，不使用泛泛而谈的形容",
            "语气与节奏要服务于目标题材",
        ]
        notes = "该预设草稿由规则化结构生成，建议创作者继续细化风格边界、禁忌表达与质量要求。"

        return PresetGenerateResponse(
            title=payload.title.strip(),
            preset_type=payload.preset_type.strip() or "文风预设",
            scope=scope,
            style_description=style_description,
            wording_tendency=wording_tendency,
            sentence_tendency=sentence_tendency,
            description_density=description_density,
            dialogue_ratio=dialogue_ratio,
            rhythm_tendency=rhythm_tendency,
            emotion_intensity=emotion_intensity,
            plot_preferences=plot_preferences,
            character_preferences=character_preferences,
            forbidden_expressions=forbidden_expressions,
            output_requirements=output_requirements,
            notes=notes,
            status=payload.status.strip() or "draft",
        )

    def test_preset(self, payload: PresetTestRequest) -> PresetTestResponse:
        validate_preset_test(payload)
        active_directives = [
            f"文风描述：{payload.style_description or '未设置'}",
            f"用词倾向：{payload.wording_tendency or '未设置'}",
            f"句式倾向：{payload.sentence_tendency or '未设置'}",
            f"描写密度：{payload.description_density or '未设置'}",
            f"对白比例：{payload.dialogue_ratio or '未设置'}",
            f"节奏倾向：{payload.rhythm_tendency or '未设置'}",
            f"情感浓度：{payload.emotion_intensity or '未设置'}",
        ]
        if payload.plot_preferences:
            active_directives.append(f"剧情偏好：{'、'.join(payload.plot_preferences)}")
        if payload.character_preferences:
            active_directives.append(f"人物塑造偏好：{'、'.join(payload.character_preferences)}")

        preview_summary = (
            f"该预设会把“{payload.sample_target or '当前生成目标'}”的表达收束到“{payload.preset_type}”方向，"
            f"重点突出{payload.rhythm_tendency or '既定节奏'}、{payload.emotion_intensity or '既定情绪强度'}与"
            f"{payload.wording_tendency or '既定用词风格'}。"
        )
        recommended_prompt = (
            f"请围绕“{payload.sample_input or '当前创作输入'}”进行创作，严格遵循以下预设："
            f"{payload.style_description or '保持既定风格'}；"
            f"用词倾向为“{payload.wording_tendency or '自然稳定'}”；"
            f"句式倾向为“{payload.sentence_tendency or '清晰可读'}”；"
            f"重点满足输出要求：{'；'.join(payload.output_requirements) or '保持一致性'}。"
        )
        quality_checklist = [
            "文风是否稳定统一",
            "表达是否具体而非空泛",
            "是否出现禁止表达",
            "剧情和人物刻画是否与预设偏好一致",
        ]
        return PresetTestResponse(
            preview_summary=preview_summary,
            recommended_prompt=recommended_prompt,
            active_directives=active_directives,
            quality_checklist=quality_checklist,
        )

    def export_preset(self, preset_id: int, export_format: str) -> dict[str, Any] | str:
        preset = self.get_preset(preset_id)
        if export_format == "json":
            return {
                "id": preset.id,
                "project_id": preset.project_id,
                "title": preset.title,
                "preset_type": preset.preset_type,
                "scope": preset.scope,
                "style_description": preset.style_description,
                "wording_tendency": preset.wording_tendency,
                "sentence_tendency": preset.sentence_tendency,
                "description_density": preset.description_density,
                "dialogue_ratio": preset.dialogue_ratio,
                "rhythm_tendency": preset.rhythm_tendency,
                "emotion_intensity": preset.emotion_intensity,
                "plot_preferences": preset.plot_preferences,
                "character_preferences": preset.character_preferences,
                "forbidden_expressions": preset.forbidden_expressions,
                "output_requirements": preset.output_requirements,
                "notes": preset.notes,
                "status": preset.status,
            }

        if export_format == "markdown":
            return self._to_markdown(preset)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported export format. Use 'json' or 'markdown'.",
        )

    def _ensure_project_exists(self, project_id: int) -> None:
        if self.project_repository.get_by_id(project_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    @staticmethod
    def _build_style_description(style_goal: str, reference_text: str) -> str:
        if style_goal:
            return f"整体风格以“{style_goal[:120]}”为核心，强调统一气质、稳定语感和可复用的表达边界。"
        if reference_text:
            return "整体风格参考样例文本的语气、节奏与意象组织方式，并进行结构化收束。"
        return "整体风格应具备稳定表达方向，避免随机漂移。"

    @staticmethod
    def _build_wording(style_goal: str) -> str:
        if any(keyword in style_goal for keyword in ["古风", "仙侠", "正剧"]):
            return "偏凝练、克制、带少量古意"
        if any(keyword in style_goal for keyword in ["轻小说", "校园", "治愈"]):
            return "偏轻快、口语化、亲近"
        if any(keyword in style_goal for keyword in ["悬疑", "黑暗", "惊悚"]):
            return "偏冷峻、压抑、细节导向"
        return "偏清晰、具体、稳定"

    @staticmethod
    def _build_sentence(style_goal: str) -> str:
        if any(keyword in style_goal for keyword in ["史诗", "奇幻", "古风"]):
            return "长短句结合，以节奏铺陈氛围"
        if any(keyword in style_goal for keyword in ["轻小说", "日常"]):
            return "中短句为主，节奏轻快"
        return "以清晰可读为主，适度变化句长"

    @staticmethod
    def _build_description_density(style_goal: str) -> str:
        if any(keyword in style_goal for keyword in ["史诗", "悬疑", "奇幻"]):
            return "中高"
        return "中"

    @staticmethod
    def _build_dialogue_ratio(style_goal: str) -> str:
        if any(keyword in style_goal for keyword in ["轻小说", "校园", "日常"]):
            return "中高"
        if any(keyword in style_goal for keyword in ["史诗", "古风正剧"]):
            return "中低"
        return "中"

    @staticmethod
    def _build_rhythm(style_goal: str) -> str:
        if any(keyword in style_goal for keyword in ["悬疑", "黑暗"]):
            return "缓慢蓄压后逐步推进"
        if any(keyword in style_goal for keyword in ["轻小说", "校园"]):
            return "轻快流畅"
        return "稳定推进"

    @staticmethod
    def _build_emotion(style_goal: str) -> str:
        if any(keyword in style_goal for keyword in ["治愈", "恋爱"]):
            return "中高"
        if any(keyword in style_goal for keyword in ["黑暗", "悬疑"]):
            return "克制但持续"
        return "中等"

    @staticmethod
    def _build_plot_preferences(style_goal: str) -> list[str]:
        if any(keyword in style_goal for keyword in ["恋爱", "治愈"]):
            return ["情感推进", "关系变化", "细节互动"]
        if any(keyword in style_goal for keyword in ["悬疑", "阴谋"]):
            return ["伏笔铺设", "信息控制", "冲突递进"]
        return ["主线清晰", "节奏稳定", "冲突明确"]

    @staticmethod
    def _build_character_preferences(style_goal: str) -> list[str]:
        if any(keyword in style_goal for keyword in ["黑暗", "悬疑"]):
            return ["强调隐藏动机", "突出细微情绪变化"]
        if any(keyword in style_goal for keyword in ["轻小说", "校园"]):
            return ["强调互动感", "突出角色辨识度"]
        return ["强调稳定人设", "突出关键动机"]

    @staticmethod
    def _to_markdown(preset: Any) -> str:
        lines = [
            f"# {preset.title}",
            "",
            f"- 类型：{preset.preset_type}",
            f"- 适用范围：{preset.scope}",
            f"- 状态：{preset.status}",
            "",
            "## 风格描述",
            "",
            preset.style_description or "暂无内容。",
            "",
            "## 核心参数",
            "",
            f"- 用词倾向：{preset.wording_tendency or '未设置'}",
            f"- 句式倾向：{preset.sentence_tendency or '未设置'}",
            f"- 描写密度：{preset.description_density or '未设置'}",
            f"- 对白比例：{preset.dialogue_ratio or '未设置'}",
            f"- 节奏倾向：{preset.rhythm_tendency or '未设置'}",
            f"- 情感浓度：{preset.emotion_intensity or '未设置'}",
            "",
            "## 剧情偏好",
            "",
            "```json",
            json.dumps(preset.plot_preferences, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 人物偏好",
            "",
            "```json",
            json.dumps(preset.character_preferences, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 禁止表达",
            "",
            "```json",
            json.dumps(preset.forbidden_expressions, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 输出要求",
            "",
            "```json",
            json.dumps(preset.output_requirements, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Notes",
            "",
            preset.notes or "暂无备注。",
            "",
        ]
        return "\n".join(lines)
