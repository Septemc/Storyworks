from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.character import (
    CharacterCreate,
    CharacterGenerateRequest,
    CharacterGenerateResponse,
    CharacterRead,
    CharacterTemplateRead,
    CharacterUpdate,
)
from app.services.character_service import CharacterService

router = APIRouter(tags=["characters"])


@router.get("/character/templates", response_model=list[CharacterTemplateRead])
def list_character_templates(db: Session = Depends(get_db)) -> list[CharacterTemplateRead]:
    service = CharacterService(db)
    return service.list_templates()


@router.get("/character/templates/{template_id}", response_model=CharacterTemplateRead)
def get_character_template(template_id: str, db: Session = Depends(get_db)) -> CharacterTemplateRead:
    service = CharacterService(db)
    return service.get_template(template_id)


@router.get("/projects/{project_id}/characters", response_model=list[CharacterRead])
def list_characters(project_id: int, db: Session = Depends(get_db)) -> list[CharacterRead]:
    service = CharacterService(db)
    return service.list_characters(project_id)


@router.post(
    "/projects/{project_id}/characters",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_character(project_id: int, payload: CharacterCreate, db: Session = Depends(get_db)) -> CharacterRead:
    service = CharacterService(db)
    return service.create_character(project_id, payload)


@router.get("/characters/{character_id}", response_model=CharacterRead)
def get_character(character_id: int, db: Session = Depends(get_db)) -> CharacterRead:
    service = CharacterService(db)
    return service.get_character(character_id)


@router.patch("/characters/{character_id}", response_model=CharacterRead)
def update_character(
    character_id: int,
    payload: CharacterUpdate,
    db: Session = Depends(get_db),
) -> CharacterRead:
    service = CharacterService(db)
    return service.update_character(character_id, payload)


@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: int, db: Session = Depends(get_db)) -> Response:
    service = CharacterService(db)
    service.delete_character(character_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/characters/generate", response_model=CharacterGenerateResponse)
def generate_character(payload: CharacterGenerateRequest, db: Session = Depends(get_db)) -> CharacterGenerateResponse:
    service = CharacterService(db)
    return service.generate_draft(payload)


@router.get("/characters/{character_id}/export")
def export_character(
    character_id: int,
    format: str = Query(default="json"),
    db: Session = Depends(get_db),
):
    service = CharacterService(db)
    exported = service.export_character(character_id, format)

    if format == "markdown":
        return PlainTextResponse(content=exported, media_type="text/markdown; charset=utf-8")

    return JSONResponse(content=exported)
