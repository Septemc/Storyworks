from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.script import ScriptDocument
from app.schemas.script import ScriptCreate, ScriptUpdate


class ScriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_project(self, project_id: int) -> list[ScriptDocument]:
        statement = (
            select(ScriptDocument)
            .where(ScriptDocument.project_id == project_id)
            .order_by(ScriptDocument.updated_at.desc(), ScriptDocument.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, script_id: int) -> ScriptDocument | None:
        return self.db.get(ScriptDocument, script_id)

    def create(self, project_id: int, payload: ScriptCreate) -> ScriptDocument:
        script = ScriptDocument(
            project_id=project_id,
            title=payload.title.strip(),
            script_type=payload.script_type.strip(),
            theme=payload.theme.strip(),
            summary=payload.summary.strip(),
            main_characters=payload.main_characters,
            core_conflict=payload.core_conflict.strip(),
            story_stage=payload.story_stage.strip(),
            major_nodes=payload.major_nodes,
            branch_ideas=payload.branch_ideas,
            forbidden_content=payload.forbidden_content.strip(),
            chapters=payload.chapters,
            scene_cards=payload.scene_cards,
            constraints=payload.constraints,
            notes=payload.notes.strip(),
            status=payload.status.strip(),
        )
        self.db.add(script)
        self.db.commit()
        self.db.refresh(script)
        return script

    def update(self, script: ScriptDocument, payload: ScriptUpdate) -> ScriptDocument:
        if payload.title is not None:
            script.title = payload.title.strip()
        if payload.script_type is not None:
            script.script_type = payload.script_type.strip()
        if payload.theme is not None:
            script.theme = payload.theme.strip()
        if payload.summary is not None:
            script.summary = payload.summary.strip()
        if payload.main_characters is not None:
            script.main_characters = payload.main_characters
        if payload.core_conflict is not None:
            script.core_conflict = payload.core_conflict.strip()
        if payload.story_stage is not None:
            script.story_stage = payload.story_stage.strip()
        if payload.major_nodes is not None:
            script.major_nodes = payload.major_nodes
        if payload.branch_ideas is not None:
            script.branch_ideas = payload.branch_ideas
        if payload.forbidden_content is not None:
            script.forbidden_content = payload.forbidden_content.strip()
        if payload.chapters is not None:
            script.chapters = payload.chapters
        if payload.scene_cards is not None:
            script.scene_cards = payload.scene_cards
        if payload.constraints is not None:
            script.constraints = payload.constraints
        if payload.notes is not None:
            script.notes = payload.notes.strip()
        if payload.status is not None:
            script.status = payload.status.strip()

        self.db.add(script)
        self.db.commit()
        self.db.refresh(script)
        return script

    def delete(self, script: ScriptDocument) -> None:
        self.db.delete(script)
        self.db.commit()
