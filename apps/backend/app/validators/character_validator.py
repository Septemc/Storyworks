from typing import Any

from fastapi import HTTPException, status

from app.schemas.character import CharacterCreate, CharacterUpdate


def _get_nested_value(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _has_meaningful_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _is_unknown_value(value: Any) -> bool:
    if isinstance(value, str):
        return "未知" in value
    return False


def _validate_status(status_value: str) -> None:
    allowed = {"draft", "ready", "final", "archived"}
    if status_value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Character status must be one of: {', '.join(sorted(allowed))}.",
        )


def validate_character_payload(
    developer_mode: dict[str, Any],
    player_mode: dict[str, Any],
    template: dict[str, Any],
) -> None:
    fields = template["config"]["fields"]
    for field in fields:
        path = field["path"]
        developer_value = _get_nested_value(developer_mode, path)
        player_value = _get_nested_value(player_mode, path)

        if not _has_meaningful_value(developer_value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Developer mode field is required: {path}",
            )

        if player_value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Player mode field is required: {path}",
            )

        if field["tab"] in {"tab_secrets", "tab_fortune"} and _has_meaningful_value(developer_value):
            if not _is_unknown_value(player_value):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Player mode field must stay unknown before reveal: {path}",
                )


def validate_character_create(payload: CharacterCreate, template: dict[str, Any]) -> None:
    if not payload.template_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Character template_id cannot be empty.",
        )

    _validate_status(payload.status)
    validate_character_payload(payload.developer_mode, payload.player_mode, template)


def validate_character_update(payload: CharacterUpdate, template: dict[str, Any]) -> None:
    if payload.status is not None:
        _validate_status(payload.status)

    if payload.developer_mode is not None and payload.player_mode is not None:
        validate_character_payload(payload.developer_mode, payload.player_mode, template)
