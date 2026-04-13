from datetime import datetime

from pydantic import BaseModel, Field


class PresetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    preset_type: str = Field(default="文风预设", max_length=64)
    scope: str = Field(default="通用", max_length=64)
    style_description: str = ""
    wording_tendency: str = Field(default="", max_length=200)
    sentence_tendency: str = Field(default="", max_length=200)
    description_density: str = Field(default="", max_length=64)
    dialogue_ratio: str = Field(default="", max_length=64)
    rhythm_tendency: str = Field(default="", max_length=120)
    emotion_intensity: str = Field(default="", max_length=120)
    plot_preferences: list[str] = Field(default_factory=list)
    character_preferences: list[str] = Field(default_factory=list)
    forbidden_expressions: list[str] = Field(default_factory=list)
    output_requirements: list[str] = Field(default_factory=list)
    notes: str = ""
    status: str = Field(default="draft", max_length=32)


class PresetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    preset_type: str | None = Field(default=None, max_length=64)
    scope: str | None = Field(default=None, max_length=64)
    style_description: str | None = None
    wording_tendency: str | None = Field(default=None, max_length=200)
    sentence_tendency: str | None = Field(default=None, max_length=200)
    description_density: str | None = Field(default=None, max_length=64)
    dialogue_ratio: str | None = Field(default=None, max_length=64)
    rhythm_tendency: str | None = Field(default=None, max_length=120)
    emotion_intensity: str | None = Field(default=None, max_length=120)
    plot_preferences: list[str] | None = None
    character_preferences: list[str] | None = None
    forbidden_expressions: list[str] | None = None
    output_requirements: list[str] | None = None
    notes: str | None = None
    status: str | None = Field(default=None, max_length=32)


class PresetRead(BaseModel):
    id: int
    project_id: int
    title: str
    preset_type: str
    scope: str
    style_description: str
    wording_tendency: str
    sentence_tendency: str
    description_density: str
    dialogue_ratio: str
    rhythm_tendency: str
    emotion_intensity: str
    plot_preferences: list[str]
    character_preferences: list[str]
    forbidden_expressions: list[str]
    output_requirements: list[str]
    notes: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PresetGenerateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    preset_type: str = Field(default="文风预设", max_length=64)
    style_goal: str = Field(default="", max_length=2000)
    reference_text: str = Field(default="", max_length=2000)
    target_use: str = Field(default="", max_length=500)
    status: str = Field(default="draft", max_length=32)


class PresetGenerateResponse(BaseModel):
    title: str
    preset_type: str
    scope: str
    style_description: str
    wording_tendency: str
    sentence_tendency: str
    description_density: str
    dialogue_ratio: str
    rhythm_tendency: str
    emotion_intensity: str
    plot_preferences: list[str]
    character_preferences: list[str]
    forbidden_expressions: list[str]
    output_requirements: list[str]
    notes: str
    status: str


class PresetTestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    preset_type: str = Field(default="文风预设", max_length=64)
    style_description: str = ""
    wording_tendency: str = ""
    sentence_tendency: str = ""
    description_density: str = ""
    dialogue_ratio: str = ""
    rhythm_tendency: str = ""
    emotion_intensity: str = ""
    plot_preferences: list[str] = Field(default_factory=list)
    character_preferences: list[str] = Field(default_factory=list)
    forbidden_expressions: list[str] = Field(default_factory=list)
    output_requirements: list[str] = Field(default_factory=list)
    sample_target: str = Field(default="", max_length=500)
    sample_input: str = Field(default="", max_length=2000)


class PresetTestResponse(BaseModel):
    preview_summary: str
    recommended_prompt: str
    active_directives: list[str]
    quality_checklist: list[str]
