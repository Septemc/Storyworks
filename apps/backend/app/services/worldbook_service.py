from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.worldbook_repository import WorldbookRepository
from app.schemas.worldbook import (
    WorldbookCreate,
    WorldbookGenerateRequest,
    WorldbookGenerateResponse,
    WorldbookRead,
    WorldbookUpdate,
)
from app.validators.worldbook_validator import (
    validate_worldbook_create,
    validate_worldbook_update,
)


class WorldbookService:
    def __init__(self, db: Session):
        self.repository = WorldbookRepository(db)
        self.project_repository = ProjectRepository(db)

    def list_entries(self, project_id: int):
        self._ensure_project_exists(project_id)
        return self.repository.list_by_project(project_id)

    def get_entry(self, entry_id: int):
        entry = self.repository.get_by_id(entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worldbook entry not found.")
        return entry

    def create_entry(self, project_id: int, payload: WorldbookCreate):
        self._ensure_project_exists(project_id)
        validate_worldbook_create(payload)
        return self.repository.create(project_id, payload)

    def update_entry(self, entry_id: int, payload: WorldbookUpdate):
        validate_worldbook_update(payload)
        entry = self.get_entry(entry_id)
        return self.repository.update(entry, payload)

    def delete_entry(self, entry_id: int) -> None:
        entry = self.get_entry(entry_id)
        self.repository.delete(entry)

    def generate_draft(self, payload: WorldbookGenerateRequest) -> WorldbookGenerateResponse:
        normalized_idea = payload.idea.strip()
        category_label = payload.category.value
        summary = f"{payload.title.strip()}是该项目中与{category_label}相关的核心设定条目。"
        if normalized_idea:
            summary = f"{payload.title.strip()}是该项目中与{category_label}相关的重要设定，核心概念围绕：{normalized_idea[:60]}。"

        keywords = self._build_keywords(payload.title, payload.category.value, normalized_idea)
        content = {
            "definition": self._build_definition(payload.title, payload.category.value, normalized_idea),
            "origin": self._build_origin(payload.category.value, normalized_idea),
            "structure": self._build_structure(payload.category.value),
            "rules": self._build_rules(payload.category.value),
            "impact": self._build_impact(payload.category.value),
        }
        notes = "该草稿由规则化模板生成，建议创作者补充更具体的世界细节与项目专属术语。"

        return WorldbookGenerateResponse(
            category=payload.category,
            title=payload.title.strip(),
            summary=summary,
            keywords=keywords,
            content=content,
            notes=notes,
            status=payload.mode.strip() or "draft",
        )

    def export_entry(self, entry_id: int, export_format: str) -> dict[str, object] | str:
        entry = self.get_entry(entry_id)
        read_model = WorldbookRead.model_validate(entry)

        if export_format == "json":
            return read_model.model_dump(mode="json")

        if export_format == "markdown":
            return self._to_markdown(read_model)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported export format. Use 'json' or 'markdown'.",
        )

    def _ensure_project_exists(self, project_id: int) -> None:
        if self.project_repository.get_by_id(project_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    @staticmethod
    def _build_keywords(title: str, category: str, idea: str) -> list[str]:
        seed = [title.strip(), category]
        if idea:
            seed.extend([segment.strip() for segment in idea.replace("，", ",").split(",") if segment.strip()])

        unique_keywords: list[str] = []
        for item in seed:
            if item and item not in unique_keywords:
                unique_keywords.append(item)
            if len(unique_keywords) >= 6:
                break
        return unique_keywords

    @staticmethod
    def _build_definition(title: str, category: str, idea: str) -> str:
        if idea:
            return f"{title.strip()}属于“{category}”分类，是围绕“{idea.strip()}”展开的重要世界设定。"
        return f"{title.strip()}属于“{category}”分类，是该世界观中的关键设定条目。"

    @staticmethod
    def _build_origin(category: str, idea: str) -> str:
        if idea:
            return f"该设定的形成与“{idea.strip()}”密切相关，建议补充其历史起源、形成动因与关键转折。"
        return f"建议从{category}脉络出发，补充该设定的起源、形成过程与历史背景。"

    @staticmethod
    def _build_structure(category: str) -> str:
        return f"建议说明该{category}设定的内部结构、组成方式、层级划分或主要构成要素。"

    @staticmethod
    def _build_rules(category: str) -> str:
        return f"建议明确该{category}设定的运作规则、限制条件、默认常识与例外情况。"

    @staticmethod
    def _build_impact(category: str) -> str:
        return f"建议说明该{category}设定会如何影响人物行动、社会秩序、剧情推进或世界气质。"

    @staticmethod
    def _to_markdown(entry: WorldbookRead) -> str:
        lines = [
            f"# {entry.title}",
            "",
            f"- 分类：{entry.category.value}",
            f"- 状态：{entry.status}",
            f"- 关键词：{', '.join(entry.keywords) if entry.keywords else '无'}",
            "",
            "## 摘要",
            "",
            entry.summary or "暂无摘要。",
            "",
            "## 定义",
            "",
            entry.content.definition or "暂无内容。",
            "",
            "## 起源",
            "",
            entry.content.origin or "暂无内容。",
            "",
            "## 结构",
            "",
            entry.content.structure or "暂无内容。",
            "",
            "## 规则",
            "",
            entry.content.rules or "暂无内容。",
            "",
            "## 影响",
            "",
            entry.content.impact or "暂无内容。",
            "",
            "## 备注",
            "",
            entry.notes or "暂无备注。",
            "",
        ]
        return "\n".join(lines)
