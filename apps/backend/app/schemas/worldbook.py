from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorldbookCategory(str, Enum):
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"
    HUMANITY = "人文"
    CUSTOMS = "风俗"
    SCIENCE = "科学"
    ECONOMY = "经济"
    RELIGION = "宗教"
    FACTION = "阵营"
    INSTITUTION = "制度"
    RACE = "种族"
    ORGANIZATION = "组织"
    EVENT = "事件"
    TERM = "术语"
    TECHNOLOGY = "技术体系"
    POWER_SYSTEM = "能力体系"


class WorldbookContent(BaseModel):
    definition: str = ""
    origin: str = ""
    structure: str = ""
    rules: str = ""
    impact: str = ""


class WorldbookCreate(BaseModel):
    category: WorldbookCategory
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=500)
    keywords: list[str] = Field(default_factory=list)
    content: WorldbookContent = Field(default_factory=WorldbookContent)
    notes: str = ""
    status: str = Field(default="draft", max_length=32)


class WorldbookUpdate(BaseModel):
    category: WorldbookCategory | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=500)
    keywords: list[str] | None = None
    content: WorldbookContent | None = None
    notes: str | None = None
    status: str | None = Field(default=None, max_length=32)


class WorldbookRead(BaseModel):
    id: int
    project_id: int
    category: WorldbookCategory
    title: str
    summary: str
    keywords: list[str]
    content: WorldbookContent
    notes: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorldbookGenerateRequest(BaseModel):
    category: WorldbookCategory
    title: str = Field(min_length=1, max_length=120)
    idea: str = Field(default="", max_length=2000)
    mode: str = Field(default="draft", max_length=32)


class WorldbookGenerateResponse(BaseModel):
    category: WorldbookCategory
    title: str
    summary: str
    keywords: list[str]
    content: WorldbookContent
    notes: str
    status: str
