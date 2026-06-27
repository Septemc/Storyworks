"""
剧本数据库
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.database import Database, get_module_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    parent_id TEXT,
    content TEXT,
    constraints TEXT,
    status TEXT DEFAULT 'draft',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS script_characters (
    script_id TEXT,
    character_id TEXT,
    role TEXT,
    PRIMARY KEY (script_id, character_id)
);

CREATE INDEX IF NOT EXISTS idx_scripts_project ON scripts(project_name);
CREATE INDEX IF NOT EXISTS idx_scripts_parent ON scripts(parent_id);
"""


def get_scripts_db(project_name: str) -> Database:
    """获取剧本数据库"""
    db = get_module_db(project_name, "scripts", "scripts.db")
    db.init_tables(SCHEMA)
    return db
