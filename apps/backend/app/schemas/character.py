from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CharacterTemplateRead(BaseModel):
    template_id: str
    name: str
    is_active: bool
    config: dict[str, Any]


class CharacterCreate(BaseModel):
    template_id: str = Field(min_length=1, max_length=120)
    developer_mode: dict[str, Any]
    player_mode: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    status: str = Field(default="draft", max_length=32)


class CharacterUpdate(BaseModel):
    developer_mode: dict[str, Any] | None = None
    player_mode: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
    notes: str | None = None
    status: str | None = Field(default=None, max_length=32)


class CharacterRead(BaseModel):
    id: int
    project_id: int
    template_id: str
    template_name: str
    name: str
    summary: str
    developer_mode: dict[str, Any]
    player_mode: dict[str, Any]
    meta: dict[str, Any]
    notes: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterGenerateRequest(BaseModel):
    template_id: str = Field(min_length=1, max_length=120)
    name_hint: str = Field(default="", max_length=120)
    concept: str = Field(default="", max_length=3000)
    project_context: str = Field(default="", max_length=1000)
    status: str = Field(default="draft", max_length=32)


class CharacterGenerateResponse(BaseModel):
    template_id: str
    template_name: str
    name: str
    summary: str
    developer_mode: dict[str, Any]
    player_mode: dict[str, Any]
    meta: dict[str, Any]
    notes: str
    status: str
