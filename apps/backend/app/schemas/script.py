from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScriptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    script_type: str = Field(default="主线", max_length=64)
    theme: str = Field(default="", max_length=160)
    summary: str = Field(default="", max_length=1000)
    main_characters: list[dict[str, Any] | str] = Field(default_factory=list)
    core_conflict: str = Field(default="", max_length=500)
    story_stage: str = Field(default="", max_length=160)
    major_nodes: list[dict[str, Any] | str] = Field(default_factory=list)
    branch_ideas: list[dict[str, Any] | str] = Field(default_factory=list)
    forbidden_content: str = ""
    chapters: list[dict[str, Any]] = Field(default_factory=list)
    scene_cards: list[dict[str, Any]] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    status: str = Field(default="draft", max_length=32)


class ScriptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    script_type: str | None = Field(default=None, max_length=64)
    theme: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=1000)
    main_characters: list[dict[str, Any] | str] | None = None
    core_conflict: str | None = Field(default=None, max_length=500)
    story_stage: str | None = Field(default=None, max_length=160)
    major_nodes: list[dict[str, Any] | str] | None = None
    branch_ideas: list[dict[str, Any] | str] | None = None
    forbidden_content: str | None = None
    chapters: list[dict[str, Any]] | None = None
    scene_cards: list[dict[str, Any]] | None = None
    constraints: dict[str, Any] | None = None
    notes: str | None = None
    status: str | None = Field(default=None, max_length=32)


class ScriptRead(BaseModel):
    id: int
    project_id: int
    title: str
    script_type: str
    theme: str
    summary: str
    main_characters: list[dict[str, Any] | str]
    core_conflict: str
    story_stage: str
    major_nodes: list[dict[str, Any] | str]
    branch_ideas: list[dict[str, Any] | str]
    forbidden_content: str
    chapters: list[dict[str, Any]]
    scene_cards: list[dict[str, Any]]
    constraints: dict[str, Any]
    notes: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScriptGenerateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    script_type: str = Field(default="主线", max_length=64)
    concept: str = Field(default="", max_length=4000)
    project_context: str = Field(default="", max_length=1000)
    status: str = Field(default="draft", max_length=32)


class ScriptGenerateResponse(BaseModel):
    title: str
    script_type: str
    theme: str
    summary: str
    main_characters: list[dict[str, Any] | str]
    core_conflict: str
    story_stage: str
    major_nodes: list[dict[str, Any] | str]
    branch_ideas: list[dict[str, Any] | str]
    forbidden_content: str
    chapters: list[dict[str, Any]]
    scene_cards: list[dict[str, Any]]
    constraints: dict[str, Any]
    notes: str
    status: str
