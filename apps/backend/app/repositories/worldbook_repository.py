from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.worldbook import WorldbookEntry
from app.schemas.worldbook import WorldbookCreate, WorldbookUpdate


class WorldbookRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_project(self, project_id: int) -> list[WorldbookEntry]:
        statement = (
            select(WorldbookEntry)
            .where(WorldbookEntry.project_id == project_id)
            .order_by(WorldbookEntry.updated_at.desc(), WorldbookEntry.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, entry_id: int) -> WorldbookEntry | None:
        return self.db.get(WorldbookEntry, entry_id)

    def create(self, project_id: int, payload: WorldbookCreate) -> WorldbookEntry:
        entry = WorldbookEntry(
            project_id=project_id,
            category=payload.category.value,
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            keywords=payload.keywords,
            content=payload.content.model_dump(),
            notes=payload.notes.strip(),
            status=payload.status.strip(),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: WorldbookEntry, payload: WorldbookUpdate) -> WorldbookEntry:
        if payload.category is not None:
            entry.category = payload.category.value
        if payload.title is not None:
            entry.title = payload.title.strip()
        if payload.summary is not None:
            entry.summary = payload.summary.strip()
        if payload.keywords is not None:
            entry.keywords = payload.keywords
        if payload.content is not None:
            entry.content = payload.content.model_dump()
        if payload.notes is not None:
            entry.notes = payload.notes.strip()
        if payload.status is not None:
            entry.status = payload.status.strip()

        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: WorldbookEntry) -> None:
        self.db.delete(entry)
        self.db.commit()
