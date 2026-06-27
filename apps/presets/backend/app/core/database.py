"""
预设数据库
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.database import Database, get_module_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS presets (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    content TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_presets_project ON presets(project_name);
"""


def get_presets_db(project_name: str) -> Database:
    """获取预设数据库"""
    db = get_module_db(project_name, "presets", "presets.db")
    db.init_tables(SCHEMA)
    return db
