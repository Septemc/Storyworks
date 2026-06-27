from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shared.config import config


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = (ROOT / "data").resolve()


def resolve_db_path() -> Path:
    configured = os.getenv("STORYWORKS_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return DATA_DIR / "storyworks.db"


DB_PATH = resolve_db_path()


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def to_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def to_json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def parse_json(value: Any, default: Any):
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


class Database:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def exec(self, sql: str, params: tuple = ()) -> int:
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount

    def script(self, sql: str):
        with self.connect() as conn:
            conn.executescript(sql)
            conn.commit()

    def one(self, sql: str, params: tuple = ()):
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def all(self, sql: str, params: tuple = ()):
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


db = Database()


def reset_configured_database_if_requested():
    if os.getenv("STORYWORKS_RESET_DB_ON_START") != "1" or not os.getenv("STORYWORKS_DB_PATH"):
        return
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{db.path}{suffix}")
        if path.exists():
            path.unlink()


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    genre TEXT,
    settings TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS worldbook_categories (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    parent_id TEXT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    template TEXT DEFAULT '{"sections":[]}',
    custom_fields TEXT DEFAULT '[]',
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_id) REFERENCES worldbook_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS worldbook_entries (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    category_id TEXT,
    title TEXT NOT NULL,
    content TEXT DEFAULT '',
    structured_data TEXT DEFAULT '{}',
    importance INTEGER DEFAULT 3 CHECK(importance BETWEEN 1 AND 5),
    visibility TEXT DEFAULT 'public',
    status TEXT DEFAULT 'draft',
    tags TEXT DEFAULT '[]',
    creator TEXT DEFAULT '',
    ai_generated INTEGER DEFAULT 0,
    ai_prompt TEXT DEFAULT '',
    ai_metadata TEXT DEFAULT '{}',
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES worldbook_categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS worldbook_relations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    label TEXT DEFAULT '',
    strength INTEGER DEFAULT 3 CHECK(strength BETWEEN 1 AND 5),
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(source_id) REFERENCES worldbook_entries(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES worldbook_entries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    character_type TEXT DEFAULT 'supporting',
    developer_data TEXT DEFAULT '{}',
    player_data TEXT DEFAULT '{}',
    field_visibility TEXT DEFAULT '{}',
    world_entry_ids TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    status TEXT DEFAULT 'active',
    ai_generated INTEGER DEFAULT 0,
    generation_history TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_relations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    direction TEXT DEFAULT 'bidirectional',
    description TEXT DEFAULT '',
    numeric_value INTEGER DEFAULT 0,
    events TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(source_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    parent_id TEXT,
    node_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT DEFAULT '',
    summary TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',
    tags TEXT DEFAULT '[]',
    importance INTEGER DEFAULT 3 CHECK(importance BETWEEN 1 AND 5),
    story_time TEXT DEFAULT '',
    story_location TEXT DEFAULT '',
    ai_generated INTEGER DEFAULT 0,
    ai_prompt TEXT DEFAULT '',
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_id) REFERENCES scripts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_references (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    script_id TEXT NOT NULL,
    ref_type TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    ref_name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(script_id) REFERENCES scripts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS presets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    dimensions TEXT DEFAULT '[]',
    custom_blocks TEXT DEFAULT '[]',
    compiled_prompt TEXT DEFAULT '',
    application_scenes TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    category TEXT DEFAULT 'general',
    ai_generated INTEGER DEFAULT 0,
    generation_input TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS version_history (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    data TEXT NOT NULL,
    summary TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_operation_logs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT DEFAULT '',
    operation TEXT NOT NULL,
    status TEXT DEFAULT 'success',
    section TEXT DEFAULT '',
    field TEXT DEFAULT '',
    instruction TEXT DEFAULT '',
    prompt TEXT DEFAULT '',
    request TEXT DEFAULT '{}',
    response_preview TEXT DEFAULT '',
    response_data TEXT DEFAULT 'null',
    process_log TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
"""

CURRENT_SCHEMA_COLUMNS = {
    "projects": [
        ("settings", "TEXT DEFAULT '{}'"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "worldbook_categories": [
        ("project_id", "TEXT DEFAULT ''"),
        ("parent_id", "TEXT"),
        ("name", "TEXT DEFAULT ''"),
        ("description", "TEXT DEFAULT ''"),
        ("template", "TEXT DEFAULT '{\"sections\":[]}'"),
        ("custom_fields", "TEXT DEFAULT '[]'"),
        ("sort_order", "INTEGER DEFAULT 0"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "worldbook_entries": [
        ("project_id", "TEXT DEFAULT ''"),
        ("category_id", "TEXT"),
        ("title", "TEXT DEFAULT ''"),
        ("content", "TEXT DEFAULT ''"),
        ("structured_data", "TEXT DEFAULT '{}'"),
        ("importance", "INTEGER DEFAULT 3"),
        ("visibility", "TEXT DEFAULT 'public'"),
        ("status", "TEXT DEFAULT 'draft'"),
        ("tags", "TEXT DEFAULT '[]'"),
        ("creator", "TEXT DEFAULT ''"),
        ("ai_generated", "INTEGER DEFAULT 0"),
        ("ai_prompt", "TEXT DEFAULT ''"),
        ("ai_metadata", "TEXT DEFAULT '{}'"),
        ("version", "INTEGER DEFAULT 1"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "worldbook_relations": [
        ("project_id", "TEXT DEFAULT ''"),
        ("source_id", "TEXT DEFAULT ''"),
        ("target_id", "TEXT DEFAULT ''"),
        ("relation_type", "TEXT DEFAULT 'related'"),
        ("label", "TEXT DEFAULT ''"),
        ("strength", "INTEGER DEFAULT 3"),
        ("description", "TEXT DEFAULT ''"),
        ("created_at", "TEXT DEFAULT ''"),
    ],
    "characters": [
        ("project_id", "TEXT DEFAULT ''"),
        ("name", "TEXT DEFAULT ''"),
        ("character_type", "TEXT DEFAULT 'supporting'"),
        ("developer_data", "TEXT DEFAULT '{}'"),
        ("player_data", "TEXT DEFAULT '{}'"),
        ("field_visibility", "TEXT DEFAULT '{}'"),
        ("world_entry_ids", "TEXT DEFAULT '[]'"),
        ("tags", "TEXT DEFAULT '[]'"),
        ("status", "TEXT DEFAULT 'active'"),
        ("ai_generated", "INTEGER DEFAULT 0"),
        ("generation_history", "TEXT DEFAULT '[]'"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "character_relations": [
        ("project_id", "TEXT DEFAULT ''"),
        ("source_id", "TEXT DEFAULT ''"),
        ("target_id", "TEXT DEFAULT ''"),
        ("relation_type", "TEXT DEFAULT 'related'"),
        ("direction", "TEXT DEFAULT 'bidirectional'"),
        ("description", "TEXT DEFAULT ''"),
        ("numeric_value", "INTEGER DEFAULT 0"),
        ("events", "TEXT DEFAULT '[]'"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "scripts": [
        ("project_id", "TEXT DEFAULT ''"),
        ("parent_id", "TEXT"),
        ("node_type", "TEXT DEFAULT 'scene'"),
        ("title", "TEXT DEFAULT ''"),
        ("content", "TEXT DEFAULT ''"),
        ("summary", "TEXT DEFAULT ''"),
        ("sort_order", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'draft'"),
        ("tags", "TEXT DEFAULT '[]'"),
        ("importance", "INTEGER DEFAULT 3"),
        ("story_time", "TEXT DEFAULT ''"),
        ("story_location", "TEXT DEFAULT ''"),
        ("ai_generated", "INTEGER DEFAULT 0"),
        ("ai_prompt", "TEXT DEFAULT ''"),
        ("version", "INTEGER DEFAULT 1"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "script_references": [
        ("project_id", "TEXT DEFAULT ''"),
        ("script_id", "TEXT DEFAULT ''"),
        ("ref_type", "TEXT DEFAULT ''"),
        ("ref_id", "TEXT DEFAULT ''"),
        ("ref_name", "TEXT DEFAULT ''"),
        ("description", "TEXT DEFAULT ''"),
        ("created_at", "TEXT DEFAULT ''"),
    ],
    "presets": [
        ("project_id", "TEXT DEFAULT ''"),
        ("name", "TEXT DEFAULT ''"),
        ("description", "TEXT DEFAULT ''"),
        ("dimensions", "TEXT DEFAULT '[]'"),
        ("custom_blocks", "TEXT DEFAULT '[]'"),
        ("compiled_prompt", "TEXT DEFAULT ''"),
        ("application_scenes", "TEXT DEFAULT '[]'"),
        ("tags", "TEXT DEFAULT '[]'"),
        ("category", "TEXT DEFAULT 'general'"),
        ("ai_generated", "INTEGER DEFAULT 0"),
        ("generation_input", "TEXT DEFAULT ''"),
        ("created_at", "TEXT DEFAULT ''"),
        ("updated_at", "TEXT DEFAULT ''"),
    ],
    "version_history": [
        ("project_id", "TEXT DEFAULT ''"),
        ("entity_type", "TEXT DEFAULT ''"),
        ("entity_id", "TEXT DEFAULT ''"),
        ("version", "INTEGER DEFAULT 1"),
        ("data", "TEXT DEFAULT '{}'"),
        ("summary", "TEXT DEFAULT ''"),
        ("created_at", "TEXT DEFAULT ''"),
    ],
    "ai_operation_logs": [
        ("project_id", "TEXT DEFAULT ''"),
        ("target_type", "TEXT DEFAULT ''"),
        ("target_id", "TEXT DEFAULT ''"),
        ("operation", "TEXT DEFAULT ''"),
        ("status", "TEXT DEFAULT 'success'"),
        ("section", "TEXT DEFAULT ''"),
        ("field", "TEXT DEFAULT ''"),
        ("instruction", "TEXT DEFAULT ''"),
        ("prompt", "TEXT DEFAULT ''"),
        ("request", "TEXT DEFAULT '{}'"),
        ("response_preview", "TEXT DEFAULT ''"),
        ("response_data", "TEXT DEFAULT 'null'"),
        ("process_log", "TEXT DEFAULT '[]'"),
        ("created_at", "TEXT DEFAULT ''"),
    ],
}

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_worldbook_entries_project ON worldbook_entries(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_worldbook_entries_category ON worldbook_entries(project_id, category_id, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_worldbook_entries_status ON worldbook_entries(project_id, status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_worldbook_relations_project ON worldbook_relations(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_worldbook_relations_pair ON worldbook_relations(project_id, source_id, target_id)",
    "CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_characters_status ON characters(project_id, status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_character_relations_project ON character_relations(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_character_relations_pair ON character_relations(project_id, source_id, target_id)",
    "CREATE INDEX IF NOT EXISTS idx_scripts_project ON scripts(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_scripts_tree ON scripts(project_id, parent_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(project_id, status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_script_refs_ref ON script_references(project_id, ref_type, ref_id)",
    "CREATE INDEX IF NOT EXISTS idx_script_refs_script ON script_references(project_id, script_id)",
    "CREATE INDEX IF NOT EXISTS idx_presets_project ON presets(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_presets_category ON presets(project_id, category, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_versions_entity ON version_history(entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_versions_project_entity ON version_history(project_id, entity_type, entity_id, version)",
    "CREATE INDEX IF NOT EXISTS idx_ai_logs_project ON ai_operation_logs(project_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_logs_target ON ai_operation_logs(project_id, target_type, target_id)",
]


DEFAULT_WORLD_CATEGORIES = [
    ("history", "历史", "时间线、事件、王朝、传说"),
    ("geography", "地理", "大陆、城市、遗迹、自然环境"),
    ("politics", "政治", "国家、制度、权力结构"),
    ("culture", "人文", "风俗、宗教、语言、艺术"),
    ("factions", "阵营", "门派、组织、商会、势力"),
    ("systems", "体系", "能力、科技、法律、经济规则"),
]


def init_database():
    reset_configured_database_if_requested()
    db.script(SCHEMA)
    run_migrations()
    seed_project()
    from .demo_data import seed_demo_content

    seed_demo_content()


def table_columns(table: str) -> set[str]:
    return {row["name"] for row in db.all(f"PRAGMA table_info({table})")}


def add_column_if_missing(table: str, column: str, definition: str):
    if column not in table_columns(table):
        db.exec(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_current_columns_and_indexes():
    for table, columns in CURRENT_SCHEMA_COLUMNS.items():
        existing_columns = table_columns(table)
        for column, definition in columns:
            if column not in existing_columns:
                db.exec(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                existing_columns.add(column)
    for statement in INDEX_STATEMENTS:
        db.exec(statement)


def migration_applied(version: int) -> bool:
    return bool(db.one("SELECT version FROM schema_migrations WHERE version = ?", (version,)))


def record_migration(version: int, name: str):
    db.exec(
        "INSERT OR IGNORE INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
        (version, name, now()),
    )


def ensure_schema_migrations_shape():
    existing_columns = table_columns("schema_migrations")
    if "name" not in existing_columns:
        db.exec("ALTER TABLE schema_migrations ADD COLUMN name TEXT DEFAULT ''")
    if "applied_at" not in existing_columns:
        db.exec("ALTER TABLE schema_migrations ADD COLUMN applied_at TEXT DEFAULT ''")


def run_migrations():
    ensure_schema_migrations_shape()
    migrations = [
        (1, "initial_unified_schema", lambda: None),
        (2, "ensure_current_columns_and_indexes", ensure_current_columns_and_indexes),
    ]
    for version, name, handler in migrations:
        if migration_applied(version):
            continue
        handler()
        record_migration(version, name)
    ensure_current_columns_and_indexes()


def seed_project():
    stamp = now()
    demos = [
        ("proj_demo", "修仙背景-demo", "修仙长篇演示项目，可直接验证世界书、人物卡、剧本、预设和 AI 迭代闭环。", "修仙"),
        ("proj_demo_urban", "都市背景-demo", "都市悬疑与现实职场演示项目，覆盖普通人角色、社会关系、线索调查和现实资源约束。", "都市"),
        ("proj_demo_scifi", "科幻背景-demo", "近未来科幻演示项目，覆盖星际设施、AI 治理、技术伦理、队伍任务和高风险选择。", "科幻"),
    ]
    for project_id, name, description, genre in demos:
        if db.one("SELECT id FROM projects WHERE id = ?", (project_id,)):
            db.exec(
                "UPDATE projects SET name = ?, description = ?, genre = ?, updated_at = ? WHERE id = ?",
                (name, description, genre, stamp, project_id),
            )
        else:
            db.exec(
                "INSERT INTO projects (id, name, description, genre, settings, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project_id, name, description, genre, "{}", stamp, stamp),
            )


def project_or_404(project_id: str) -> dict:
    project = db.one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def record_version(project_id: str, entity_type: str, entity_id: str, version: int, data: dict, summary: str = ""):
    db.exec(
        """INSERT INTO version_history (id, project_id, entity_type, entity_id, version, data, summary, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (new_id("ver"), project_id, entity_type, entity_id, version, to_json(data), summary, now()),
    )


def compile_preset(dimensions: list[dict], custom_blocks: list[dict], application_scenes: list[dict] | None = None) -> str:
    lines = ["[系统提示]", "请遵循以下创作预设。", ""]
    if dimensions:
        lines.append("[风格维度]")
        for item in sorted(dimensions, key=lambda x: x.get("order", 0)):
            name = item.get("name", "未命名维度")
            value = item.get("value", "")
            description = item.get("description", "")
            examples = item.get("examples") or []
            lines.append(f"- {name}: {value}")
            if description:
                lines.append(f"  说明: {description}")
            if examples:
                lines.append(f"  示例: {' / '.join(map(str, examples))}")
        lines.append("")
    before = [b for b in custom_blocks if b.get("position") == "before"]
    after = [b for b in custom_blocks if b.get("position") != "before"]
    for title, blocks in [("[前置要求]", before), ("[补充要求]", after)]:
        if blocks:
            lines.append(title)
            for block in sorted(blocks, key=lambda x: x.get("order", 0)):
                lines.append(f"{block.get('title', '自定义内容')}: {block.get('content', '')}")
            lines.append("")
    if application_scenes:
        lines.append("[应用场景]")
        for scene in application_scenes:
            if scene.get("enabled", True):
                lines.append(f"- {scene.get('sceneType', scene.get('scene_type', '通用'))}: {scene.get('adjustments', '')}")
    return "\n".join(lines).strip()
