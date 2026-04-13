from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.worldbook import (
    WorldbookCreate,
    WorldbookGenerateRequest,
    WorldbookGenerateResponse,
    WorldbookRead,
    WorldbookUpdate,
)
from app.services.worldbook_service import WorldbookService

router = APIRouter(tags=["worldbook"])


@router.get("/projects/{project_id}/worldbook", response_model=list[WorldbookRead])
def list_worldbook_entries(project_id: int, db: Session = Depends(get_db)) -> list[WorldbookRead]:
    service = WorldbookService(db)
    return service.list_entries(project_id)


@router.post(
    "/projects/{project_id}/worldbook",
    response_model=WorldbookRead,
    status_code=status.HTTP_201_CREATED,
)
def create_worldbook_entry(
    project_id: int,
    payload: WorldbookCreate,
    db: Session = Depends(get_db),
) -> WorldbookRead:
    service = WorldbookService(db)
    return service.create_entry(project_id, payload)


@router.get("/worldbook/{entry_id}", response_model=WorldbookRead)
def get_worldbook_entry(entry_id: int, db: Session = Depends(get_db)) -> WorldbookRead:
    service = WorldbookService(db)
    return service.get_entry(entry_id)


@router.patch("/worldbook/{entry_id}", response_model=WorldbookRead)
def update_worldbook_entry(
    entry_id: int,
    payload: WorldbookUpdate,
    db: Session = Depends(get_db),
) -> WorldbookRead:
    service = WorldbookService(db)
    return service.update_entry(entry_id, payload)


@router.delete("/worldbook/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worldbook_entry(entry_id: int, db: Session = Depends(get_db)) -> Response:
    service = WorldbookService(db)
    service.delete_entry(entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/worldbook/generate", response_model=WorldbookGenerateResponse)
def generate_worldbook_draft(
    payload: WorldbookGenerateRequest,
    db: Session = Depends(get_db),
) -> WorldbookGenerateResponse:
    service = WorldbookService(db)
    return service.generate_draft(payload)


@router.get("/worldbook/{entry_id}/export")
def export_worldbook_entry(
    entry_id: int,
    format: str = Query(default="json"),
    db: Session = Depends(get_db),
):
    service = WorldbookService(db)
    exported = service.export_entry(entry_id, format)

    if format == "markdown":
        return PlainTextResponse(content=exported, media_type="text/markdown; charset=utf-8")

    return JSONResponse(content=exported)
