from fastapi import HTTPException, status

from app.schemas.preset import PresetCreate, PresetTestRequest, PresetUpdate


def _validate_status(status_value: str) -> None:
    allowed = {"draft", "ready", "final", "archived"}
    if status_value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Preset status must be one of: {', '.join(sorted(allowed))}.",
        )


def _validate_list_length(values: list[str], field_name: str) -> None:
    if len(values) > 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} cannot exceed 12 items.",
        )


def validate_preset_create(payload: PresetCreate) -> None:
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Preset title cannot be empty.",
        )
    _validate_status(payload.status)
    _validate_list_length(payload.plot_preferences, "plot_preferences")
    _validate_list_length(payload.character_preferences, "character_preferences")
    _validate_list_length(payload.forbidden_expressions, "forbidden_expressions")
    _validate_list_length(payload.output_requirements, "output_requirements")


def validate_preset_update(payload: PresetUpdate) -> None:
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Preset title cannot be empty.",
        )
    if payload.status is not None:
        _validate_status(payload.status)
    if payload.plot_preferences is not None:
        _validate_list_length(payload.plot_preferences, "plot_preferences")
    if payload.character_preferences is not None:
        _validate_list_length(payload.character_preferences, "character_preferences")
    if payload.forbidden_expressions is not None:
        _validate_list_length(payload.forbidden_expressions, "forbidden_expressions")
    if payload.output_requirements is not None:
        _validate_list_length(payload.output_requirements, "output_requirements")


def validate_preset_test(payload: PresetTestRequest) -> None:
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Preset title cannot be empty.",
        )
