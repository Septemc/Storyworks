from fastapi import HTTPException, status

from app.schemas.worldbook import WorldbookCreate, WorldbookUpdate


def _validate_keywords(keywords: list[str]) -> None:
    if len(keywords) > 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Worldbook keywords cannot exceed 12 items.",
        )

    for keyword in keywords:
        if not keyword.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Worldbook keywords cannot contain empty values.",
            )


def _validate_status(status_value: str) -> None:
    allowed = {"draft", "ready", "final", "archived"}
    if status_value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Worldbook status must be one of: {', '.join(sorted(allowed))}.",
        )


def validate_worldbook_create(payload: WorldbookCreate) -> None:
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Worldbook title cannot be empty.",
        )

    _validate_keywords(payload.keywords)
    _validate_status(payload.status)


def validate_worldbook_update(payload: WorldbookUpdate) -> None:
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Worldbook title cannot be empty.",
        )

    if payload.keywords is not None:
        _validate_keywords(payload.keywords)

    if payload.status is not None:
        _validate_status(payload.status)
