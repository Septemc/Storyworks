from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScriptDocument(Base):
    __tablename__ = "script_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    script_type: Mapped[str] = mapped_column(String(64), default="主线", nullable=False)
    theme: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    main_characters: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    core_conflict: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    story_stage: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    major_nodes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    branch_ideas: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    forbidden_content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    chapters: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    scene_cards: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
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
