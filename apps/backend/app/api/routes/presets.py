from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.preset import (
    PresetCreate,
    PresetGenerateRequest,
    PresetGenerateResponse,
    PresetRead,
    PresetTestRequest,
    PresetTestResponse,
    PresetUpdate,
)
from app.services.preset_service import PresetService

router = APIRouter(tags=["presets"])


@router.get("/projects/{project_id}/presets", response_model=list[PresetRead])
def list_presets(project_id: int, db: Session = Depends(get_db)) -> list[PresetRead]:
    service = PresetService(db)
    return service.list_presets(project_id)


@router.post("/projects/{project_id}/presets", response_model=PresetRead, status_code=status.HTTP_201_CREATED)
def create_preset(project_id: int, payload: PresetCreate, db: Session = Depends(get_db)) -> PresetRead:
    service = PresetService(db)
    return service.create_preset(project_id, payload)


@router.get("/presets/{preset_id}", response_model=PresetRead)
def get_preset(preset_id: int, db: Session = Depends(get_db)) -> PresetRead:
    service = PresetService(db)
    return service.get_preset(preset_id)


@router.patch("/presets/{preset_id}", response_model=PresetRead)
def update_preset(preset_id: int, payload: PresetUpdate, db: Session = Depends(get_db)) -> PresetRead:
    service = PresetService(db)
    return service.update_preset(preset_id, payload)


@router.delete("/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preset(preset_id: int, db: Session = Depends(get_db)) -> Response:
    service = PresetService(db)
    service.delete_preset(preset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/presets/generate", response_model=PresetGenerateResponse)
def generate_preset(payload: PresetGenerateRequest, db: Session = Depends(get_db)) -> PresetGenerateResponse:
    service = PresetService(db)
    return service.generate_draft(payload)


@router.post("/presets/test", response_model=PresetTestResponse)
def test_preset(payload: PresetTestRequest, db: Session = Depends(get_db)) -> PresetTestResponse:
    service = PresetService(db)
    return service.test_preset(payload)


@router.get("/presets/{preset_id}/export")
def export_preset(preset_id: int, format: str = Query(default="json"), db: Session = Depends(get_db)):
    service = PresetService(db)
    exported = service.export_preset(preset_id, format)
    if format == "markdown":
        return PlainTextResponse(content=exported, media_type="text/markdown; charset=utf-8")
    return JSONResponse(content=exported)
