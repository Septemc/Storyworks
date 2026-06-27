"""
Storyworks 数据库工具
"""
import sqlite3
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class Database:
    """SQLite 数据库封装"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()

    def _ensure_dir(self):
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_tables(self, schema: str):
        """初始化表结构"""
        conn = self.get_connection()
        try:
            conn.executescript(schema)
            conn.commit()
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        finally:
            conn.close()

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """查询单条记录"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        """查询多条记录"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    import uuid

    short_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{short_id}" if prefix else short_id


def get_project_path(project_name: str, module: str) -> Path:
    """获取项目模块数据路径"""
    from .config import config

    projects_dir = Path(config.projects_dir)
    return projects_dir / project_name / module


def get_module_db(project_name: str, module: str, db_name: str) -> Database:
    """获取模块数据库"""
    db_path = get_project_path(project_name, module) / db_name
    return Database(str(db_path))


def read_other_module_data(
    project_name: str, module: str, db_name: str, sql: str, params: tuple = ()
) -> list[dict]:
    """读取其他模块的数据"""
    db = get_module_db(project_name, module, db_name)
    return db.fetch_all(sql, params)
