"""
世界书业务逻辑
"""
import json
from typing import Optional
from datetime import datetime

from shared.database import generate_id
from shared.ai_service import ai_service
from shared.prompts import prompt_templates
from app.core.database import get_worldbook_db


class WorldbookService:
    """世界书服务"""

    def list_entries(
        self,
        project_name: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """获取条目列表"""
        db = get_worldbook_db(project_name)

        sql = "SELECT * FROM worldbook_entries WHERE project_name = ?"
        params = [project_name]

        if category:
            sql += " AND category = ?"
            params.append(category)

        if status:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY updated_at DESC"

        entries = db.fetch_all(sql, tuple(params))

        # 解析 JSON 字段
        for entry in entries:
            entry["keywords"] = json.loads(entry.get("keywords") or "[]")
            entry["relations"] = json.loads(entry.get("relations") or "[]")

        return entries

    def get_entry(self, project_name: str, entry_id: str) -> Optional[dict]:
        """获取条目详情"""
        db = get_worldbook_db(project_name)
        entry = db.fetch_one(
            "SELECT * FROM worldbook_entries WHERE id = ? AND project_name = ?",
            (entry_id, project_name),
        )
        if entry:
            entry["keywords"] = json.loads(entry.get("keywords") or "[]")
            entry["relations"] = json.loads(entry.get("relations") or "[]")
        return entry

    def create_entry(
        self,
        project_name: str,
        category: str,
        title: str,
        summary: str = None,
        content: str = None,
        keywords: list[str] = None,
        relations: list[str] = None,
        notes: str = None,
    ) -> dict:
        """创建条目"""
        db = get_worldbook_db(project_name)
        entry_id = generate_id("world")
        now = datetime.now().isoformat()

        db.execute(
            """INSERT INTO worldbook_entries
               (id, project_name, category, title, summary, content, keywords, relations, notes, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                project_name,
                category,
                title,
                summary,
                content,
                json.dumps(keywords or [], ensure_ascii=False),
                json.dumps(relations or [], ensure_ascii=False),
                notes,
                "draft",
                now,
                now,
            ),
        )

        return self.get_entry(project_name, entry_id)

    def update_entry(
        self,
        project_name: str,
        entry_id: str,
        **kwargs,
    ) -> Optional[dict]:
        """更新条目"""
        db = get_worldbook_db(project_name)

        # 检查是否存在
        existing = db.fetch_one(
            "SELECT id FROM worldbook_entries WHERE id = ? AND project_name = ?",
            (entry_id, project_name),
        )
        if not existing:
            return None

        # 构建更新语句
        updates = []
        params = []

        field_map = {
            "category": "category",
            "title": "title",
            "summary": "summary",
            "content": "content",
            "notes": "notes",
            "status": "status",
        }

        for field, column in field_map.items():
            if field in kwargs and kwargs[field] is not None:
                updates.append(f"{column} = ?")
                params.append(kwargs[field])

        if "keywords" in kwargs and kwargs["keywords"] is not None:
            updates.append("keywords = ?")
            params.append(json.dumps(kwargs["keywords"], ensure_ascii=False))

        if "relations" in kwargs and kwargs["relations"] is not None:
            updates.append("relations = ?")
            params.append(json.dumps(kwargs["relations"], ensure_ascii=False))

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.extend([entry_id, project_name])

            sql = f"UPDATE worldbook_entries SET {', '.join(updates)} WHERE id = ? AND project_name = ?"
            db.execute(sql, tuple(params))

        return self.get_entry(project_name, entry_id)

    def delete_entry(self, project_name: str, entry_id: str) -> bool:
        """删除条目"""
        db = get_worldbook_db(project_name)
        cursor = db.execute(
            "DELETE FROM worldbook_entries WHERE id = ? AND project_name = ?",
            (entry_id, project_name),
        )
        return cursor.rowcount > 0

    def list_blueprints(self, project_name: str) -> list[dict]:
        """获取蓝图列表"""
        db = get_worldbook_db(project_name)
        return db.fetch_all(
            "SELECT * FROM world_blueprints WHERE project_name = ? ORDER BY created_at DESC",
            (project_name,),
        )

    def create_blueprint(
        self,
        project_name: str,
        name: str,
        description: str = None,
        content: str = None,
    ) -> dict:
        """创建蓝图"""
        db = get_worldbook_db(project_name)
        blueprint_id = generate_id("bp")
        now = datetime.now().isoformat()

        db.execute(
            """INSERT INTO world_blueprints (id, project_name, name, description, content, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (blueprint_id, project_name, name, description, content, now),
        )

        return {
            "id": blueprint_id,
            "project_name": project_name,
            "name": name,
            "description": description,
            "content": content,
            "created_at": now,
        }

    async def generate_entry(
        self,
        project_name: str,
        category: str,
        title: str,
        summary: str = None,
    ) -> dict:
        """AI 生成世界书条目"""
        # 获取已有条目作为上下文
        existing_entries = self.list_entries(project_name, category)
        context = ""
        if existing_entries:
            context = "已有同类条目：\n"
            for entry in existing_entries[:3]:
                context += f"- {entry['title']}: {entry.get('summary', '')}\n"

        # 渲染 Prompt
        prompt = prompt_templates.render(
            "worldbook",
            "generate_entry",
            category=category,
            title=title,
            summary=summary or "待补充",
            context=context,
        )

        system_prompt = "你是一个专业的世界观设定助手，擅长创建详细、一致的世界设定。请直接输出内容，不要添加额外说明。"

        # 调用 AI
        generated_content = await ai_service.generate(prompt, system_prompt)

        return {
            "category": category,
            "title": title,
            "summary": summary,
            "content": generated_content,
            "status": "draft",
        }
