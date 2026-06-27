"""
项目管理业务逻辑
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from shared.database import generate_id, Database
from shared.config import config


class ProjectService:
    """项目管理服务"""

    def __init__(self):
        self.projects_dir = Path(config.projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        from app.core.database import init_database, get_projects_db

        init_database()
        self.db = get_projects_db()

    def list_projects(self) -> list[dict]:
        """获取项目列表"""
        projects = self.db.fetch_all(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        )
        # 添加模块信息
        for project in projects:
            project_path = self.projects_dir / project["name"]
            project["modules"] = self._get_project_modules(project_path)
        return projects

    def get_project(self, project_id: str) -> Optional[dict]:
        """获取项目详情"""
        project = self.db.fetch_one(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        )
        if project:
            project_path = self.projects_dir / project["name"]
            project["modules"] = self._get_project_modules(project_path)
        return project

    def create_project(
        self,
        name: str,
        description: str = None,
        genre: str = None,
    ) -> dict:
        """创建新项目"""
        # 检查名称是否重复
        existing = self.db.fetch_one(
            "SELECT id FROM projects WHERE name = ?", (name,)
        )
        if existing:
            raise ValueError(f"项目名称已存在: {name}")

        # 创建项目目录
        project_path = self.projects_dir / name
        if project_path.exists():
            raise ValueError(f"项目目录已存在: {name}")

        # 创建目录结构
        self._create_project_structure(project_path)

        # 保存到数据库
        project_id = generate_id("proj")
        now = datetime.now().isoformat()

        self.db.execute(
            """INSERT INTO projects (id, name, description, genre, settings, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project_id, name, description, genre, "{}", now, now),
        )

        return {
            "id": project_id,
            "name": name,
            "description": description,
            "genre": genre,
            "created_at": now,
        }

    def update_project(
        self,
        project_id: str,
        name: str = None,
        description: str = None,
        genre: str = None,
        settings: dict = None,
    ) -> Optional[dict]:
        """更新项目"""
        project = self.db.fetch_one(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        )
        if not project:
            return None

        updates = []
        params = []

        if name is not None:
            # 检查新名称是否重复
            existing = self.db.fetch_one(
                "SELECT id FROM projects WHERE name = ? AND id != ?",
                (name, project_id),
            )
            if existing:
                raise ValueError(f"项目名称已存在: {name}")
            updates.append("name = ?")
            params.append(name)

            # 重命名目录
            old_path = self.projects_dir / project["name"]
            new_path = self.projects_dir / name
            if old_path.exists():
                old_path.rename(new_path)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if genre is not None:
            updates.append("genre = ?")
            params.append(genre)

        if settings is not None:
            updates.append("settings = ?")
            params.append(json.dumps(settings, ensure_ascii=False))

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(project_id)

            sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
            self.db.execute(sql, tuple(params))

        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project = self.db.fetch_one(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        )
        if not project:
            return False

        # 删除数据库记录
        self.db.execute("DELETE FROM projects WHERE id = ?", (project_id,))

        # 删除项目目录（可选，保留数据）
        # project_path = self.projects_dir / project["name"]
        # if project_path.exists():
        #     shutil.rmtree(project_path)

        return True

    def _create_project_structure(self, project_path: Path):
        """创建项目目录结构"""
        dirs = [
            "worldbook",
            "characters",
            "scripts",
            "presets",
            "templates/worldbook",
            "templates/characters",
            "templates/scripts",
            "templates/presets",
        ]
        for d in dirs:
            (project_path / d).mkdir(parents=True, exist_ok=True)

        # 创建项目元数据
        project_meta = {
            "created_at": datetime.now().isoformat(),
            "modules": ["worldbook", "characters", "scripts", "presets"],
        }
        (project_path / "project.json").write_text(
            json.dumps(project_meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_project_modules(self, project_path: Path) -> list[dict]:
        """获取项目已初始化的模块"""
        modules = []
        module_map = {
            "worldbook": {"name": "世界书", "port": 8001},
            "characters": {"name": "人物卡", "port": 8002},
            "scripts": {"name": "剧本", "port": 8003},
            "presets": {"name": "预设", "port": 8004},
        }

        for module_id, info in module_map.items():
            module_path = project_path / module_id
            if module_path.exists():
                modules.append({
                    "id": module_id,
                    "name": info["name"],
                    "port": info["port"],
                    "initialized": True,
                })

        return modules
