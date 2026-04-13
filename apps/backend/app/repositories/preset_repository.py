from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preset import PresetProfile
from app.schemas.preset import PresetCreate, PresetUpdate


class PresetRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_project(self, project_id: int) -> list[PresetProfile]:
        statement = (
            select(PresetProfile)
            .where(PresetProfile.project_id == project_id)
            .order_by(PresetProfile.updated_at.desc(), PresetProfile.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, preset_id: int) -> PresetProfile | None:
        return self.db.get(PresetProfile, preset_id)

    def create(self, project_id: int, payload: PresetCreate) -> PresetProfile:
        preset = PresetProfile(
            project_id=project_id,
            title=payload.title.strip(),
            preset_type=payload.preset_type.strip(),
            scope=payload.scope.strip(),
            style_description=payload.style_description.strip(),
            wording_tendency=payload.wording_tendency.strip(),
            sentence_tendency=payload.sentence_tendency.strip(),
            description_density=payload.description_density.strip(),
            dialogue_ratio=payload.dialogue_ratio.strip(),
            rhythm_tendency=payload.rhythm_tendency.strip(),
            emotion_intensity=payload.emotion_intensity.strip(),
            plot_preferences=payload.plot_preferences,
            character_preferences=payload.character_preferences,
            forbidden_expressions=payload.forbidden_expressions,
            output_requirements=payload.output_requirements,
            notes=payload.notes.strip(),
            status=payload.status.strip(),
        )
        self.db.add(preset)
        self.db.commit()
        self.db.refresh(preset)
        return preset

    def update(self, preset: PresetProfile, payload: PresetUpdate) -> PresetProfile:
        if payload.title is not None:
            preset.title = payload.title.strip()
        if payload.preset_type is not None:
            preset.preset_type = payload.preset_type.strip()
        if payload.scope is not None:
            preset.scope = payload.scope.strip()
        if payload.style_description is not None:
            preset.style_description = payload.style_description.strip()
        if payload.wording_tendency is not None:
            preset.wording_tendency = payload.wording_tendency.strip()
        if payload.sentence_tendency is not None:
            preset.sentence_tendency = payload.sentence_tendency.strip()
        if payload.description_density is not None:
            preset.description_density = payload.description_density.strip()
        if payload.dialogue_ratio is not None:
            preset.dialogue_ratio = payload.dialogue_ratio.strip()
        if payload.rhythm_tendency is not None:
            preset.rhythm_tendency = payload.rhythm_tendency.strip()
        if payload.emotion_intensity is not None:
            preset.emotion_intensity = payload.emotion_intensity.strip()
        if payload.plot_preferences is not None:
            preset.plot_preferences = payload.plot_preferences
        if payload.character_preferences is not None:
            preset.character_preferences = payload.character_preferences
        if payload.forbidden_expressions is not None:
            preset.forbidden_expressions = payload.forbidden_expressions
        if payload.output_requirements is not None:
            preset.output_requirements = payload.output_requirements
        if payload.notes is not None:
            preset.notes = payload.notes.strip()
        if payload.status is not None:
            preset.status = payload.status.strip()

        self.db.add(preset)
        self.db.commit()
        self.db.refresh(preset)
        return preset

    def delete(self, preset: PresetProfile) -> None:
        self.db.delete(preset)
        self.db.commit()
