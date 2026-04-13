from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate
from app.validators.project_validator import validate_project_create


class ProjectService:
    def __init__(self, db: Session):
        self.repository = ProjectRepository(db)

    def list_projects(self):
        return self.repository.list_all()

    def create_project(self, payload: ProjectCreate):
        validate_project_create(payload)
        return self.repository.create(payload)
