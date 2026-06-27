"""
世界书数据库
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.database import Database, get_module_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS worldbook_entries (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    keywords TEXT DEFAULT '[]',
    relations TEXT DEFAULT '[]',
    notes TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS world_blueprints (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entries_project ON worldbook_entries(project_name);
CREATE INDEX IF NOT EXISTS idx_entries_category ON worldbook_entries(category);
CREATE INDEX IF NOT EXISTS idx_blueprints_project ON world_blueprints(project_name);
"""


def get_worldbook_db(project_name: str) -> Database:
    """获取世界书数据库"""
    db = get_module_db(project_name, "worldbook", "worldbook.db")
    db.init_tables(SCHEMA)
    return db
