"""
项目管理数据库初始化
"""
import sys
from pathlib import Path

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.database import Database, get_module_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    genre TEXT,
    settings TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_database():
    """初始化项目管理数据库"""
    from shared.config import config

    projects_dir = Path(config.projects_dir)
    projects_dir.mkdir(parents=True, exist_ok=True)

    db_path = projects_dir / "projects.db"
    db = Database(str(db_path))
    db.init_tables(SCHEMA)
    print(f"项目管理数据库已初始化: {db_path}")


def get_projects_db() -> Database:
    """获取项目管理数据库"""
    from shared.config import config

    db_path = Path(config.projects_dir) / "projects.db"
    return Database(str(db_path))
