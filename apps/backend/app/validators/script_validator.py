from fastapi import HTTPException, status

from app.schemas.script import ScriptCreate, ScriptUpdate


def _validate_status(status_value: str) -> None:
    allowed = {"draft", "ready", "final", "archived"}
    if status_value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Script status must be one of: {', '.join(sorted(allowed))}.",
        )


def _validate_scene_cards(scene_cards: list[dict]) -> None:
    for index, scene in enumerate(scene_cards):
        required_keys = {"title", "goal", "location", "participants", "must_happen"}
        missing = [key for key in required_keys if key not in scene]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Scene card #{index + 1} is missing keys: {', '.join(missing)}",
            )


def validate_script_create(payload: ScriptCreate) -> None:
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Script title cannot be empty.",
        )
    _validate_status(payload.status)
    _validate_scene_cards(payload.scene_cards)


def validate_script_update(payload: ScriptUpdate) -> None:
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Script title cannot be empty.",
        )
    if payload.status is not None:
        _validate_status(payload.status)
    if payload.scene_cards is not None:
        _validate_scene_cards(payload.scene_cards)
