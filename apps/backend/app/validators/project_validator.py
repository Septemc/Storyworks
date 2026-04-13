from fastapi import HTTPException, status

from app.schemas.project import ProjectCreate


def validate_project_create(payload: ProjectCreate) -> None:
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project title cannot be empty.",
        )
