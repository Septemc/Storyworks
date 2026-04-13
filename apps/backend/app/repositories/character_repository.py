from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.character import CharacterProfile
from app.schemas.character import CharacterCreate, CharacterUpdate


class CharacterRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_project(self, project_id: int) -> list[CharacterProfile]:
        statement = (
            select(CharacterProfile)
            .where(CharacterProfile.project_id == project_id)
            .order_by(CharacterProfile.updated_at.desc(), CharacterProfile.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, character_id: int) -> CharacterProfile | None:
        return self.db.get(CharacterProfile, character_id)

    def create(
        self,
        project_id: int,
        template_name: str,
        name: str,
        summary: str,
        payload: CharacterCreate,
    ) -> CharacterProfile:
        character = CharacterProfile(
            project_id=project_id,
            template_id=payload.template_id.strip(),
            template_name=template_name,
            name=name,
            summary=summary,
            developer_mode=payload.developer_mode,
            player_mode=payload.player_mode,
            meta=payload.meta,
            notes=payload.notes.strip(),
            status=payload.status.strip(),
        )
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        return character

    def update(
        self,
        character: CharacterProfile,
        name: str | None,
        summary: str | None,
        payload: CharacterUpdate,
    ) -> CharacterProfile:
        if payload.developer_mode is not None:
            character.developer_mode = payload.developer_mode
        if payload.player_mode is not None:
            character.player_mode = payload.player_mode
        if payload.meta is not None:
            character.meta = payload.meta
        if payload.notes is not None:
            character.notes = payload.notes.strip()
        if payload.status is not None:
            character.status = payload.status.strip()
        if name is not None:
            character.name = name
        if summary is not None:
            character.summary = summary

        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        return character

    def delete(self, character: CharacterProfile) -> None:
        self.db.delete(character)
        self.db.commit()
