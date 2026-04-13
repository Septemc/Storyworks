from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Project]:
        statement = select(Project).order_by(Project.updated_at.desc(), Project.id.desc())
        return list(self.db.scalars(statement).all())

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def create(self, payload: ProjectCreate) -> Project:
        project = Project(title=payload.title.strip(), summary=payload.summary.strip())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
