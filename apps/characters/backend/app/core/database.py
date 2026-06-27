"""
人物卡数据库
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.database import Database, get_module_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    template_id TEXT,
    name TEXT NOT NULL,
    developer_mode TEXT,
    player_mode TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS character_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    structure TEXT,
    is_builtin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_name);
"""


def get_characters_db(project_name: str) -> Database:
    """获取人物卡数据库"""
    db = get_module_db(project_name, "characters", "characters.db")
    db.init_tables(SCHEMA)
    return db
