from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=500)


class ProjectRead(BaseModel):
    id: int
    title: str
    summary: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
