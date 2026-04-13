from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.models.character import CharacterProfile  # noqa: F401
from app.models.preset import PresetProfile  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.script import ScriptDocument  # noqa: F401
from app.models.worldbook import WorldbookEntry  # noqa: F401

engine_kwargs = {}
if settings.resolved_database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.resolved_database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
