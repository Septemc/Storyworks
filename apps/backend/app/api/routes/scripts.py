from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.script import (
    ScriptCreate,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptRead,
    ScriptUpdate,
)
from app.services.script_service import ScriptService

router = APIRouter(tags=["scripts"])


@router.get("/projects/{project_id}/scripts", response_model=list[ScriptRead])
def list_scripts(project_id: int, db: Session = Depends(get_db)) -> list[ScriptRead]:
    service = ScriptService(db)
    return service.list_scripts(project_id)


@router.post("/projects/{project_id}/scripts", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
def create_script(project_id: int, payload: ScriptCreate, db: Session = Depends(get_db)) -> ScriptRead:
    service = ScriptService(db)
    return service.create_script(project_id, payload)


@router.get("/scripts/{script_id}", response_model=ScriptRead)
def get_script(script_id: int, db: Session = Depends(get_db)) -> ScriptRead:
    service = ScriptService(db)
    return service.get_script(script_id)


@router.patch("/scripts/{script_id}", response_model=ScriptRead)
def update_script(script_id: int, payload: ScriptUpdate, db: Session = Depends(get_db)) -> ScriptRead:
    service = ScriptService(db)
    return service.update_script(script_id, payload)


@router.delete("/scripts/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_script(script_id: int, db: Session = Depends(get_db)) -> Response:
    service = ScriptService(db)
    service.delete_script(script_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/scripts/generate", response_model=ScriptGenerateResponse)
def generate_script(payload: ScriptGenerateRequest, db: Session = Depends(get_db)) -> ScriptGenerateResponse:
    service = ScriptService(db)
    return service.generate_draft(payload)


@router.get("/scripts/{script_id}/export")
def export_script(script_id: int, format: str = Query(default="json"), db: Session = Depends(get_db)):
    service = ScriptService(db)
    exported = service.export_script(script_id, format)
    if format == "markdown":
        return PlainTextResponse(content=exported, media_type="text/markdown; charset=utf-8")
    return JSONResponse(content=exported)
