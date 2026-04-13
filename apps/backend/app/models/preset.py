from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PresetProfile(Base):
    __tablename__ = "preset_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    preset_type: Mapped[str] = mapped_column(String(64), default="文风预设", nullable=False)
    scope: Mapped[str] = mapped_column(String(64), default="通用", nullable=False)
    style_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    wording_tendency: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    sentence_tendency: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    description_density: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    dialogue_ratio: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    rhythm_tendency: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    emotion_intensity: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    plot_preferences: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    character_preferences: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    forbidden_expressions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    output_requirements: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
