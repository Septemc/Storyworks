"""
预设业务逻辑
"""
import json
from typing import Optional
from datetime import datetime

from shared.database import generate_id
from shared.ai_service import ai_service
from shared.prompts import prompt_templates
from app.core.database import get_presets_db


class PresetService:
    """预设服务"""

    def list_presets(
        self,
        project_name: str,
        category: Optional[str] = None,
    ) -> list[dict]:
        """获取预设列表"""
        db = get_presets_db(project_name)

        sql = "SELECT * FROM presets WHERE project_name = ?"
        params = [project_name]

        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " ORDER BY updated_at DESC"

        presets = db.fetch_all(sql, tuple(params))

        for preset in presets:
            preset["content"] = json.loads(preset.get("content") or "{}")

        return presets

    def get_preset(self, project_name: str, preset_id: str) -> Optional[dict]:
        """获取预设详情"""
        db = get_presets_db(project_name)
        preset = db.fetch_one(
            "SELECT * FROM presets WHERE id = ? AND project_name = ?",
            (preset_id, project_name),
        )
        if preset:
            preset["content"] = json.loads(preset.get("content") or "{}")
        return preset

    def create_preset(
        self,
        project_name: str,
        name: str,
        category: str = None,
        description: str = None,
        content: dict = None,
    ) -> dict:
        """创建预设"""
        db = get_presets_db(project_name)
        preset_id = generate_id("preset")
        now = datetime.now().isoformat()

        db.execute(
            """INSERT INTO presets
               (id, project_name, name, category, description, content, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                preset_id,
                project_name,
                name,
                category,
                description,
                json.dumps(content or {}, ensure_ascii=False),
                "draft",
                now,
                now,
            ),
        )

        return self.get_preset(project_name, preset_id)

    def update_preset(
        self,
        project_name: str,
        preset_id: str,
        **kwargs,
    ) -> Optional[dict]:
        """更新预设"""
        db = get_presets_db(project_name)

        existing = db.fetch_one(
            "SELECT id FROM presets WHERE id = ? AND project_name = ?",
            (preset_id, project_name),
        )
        if not existing:
            return None

        updates = []
        params = []

        if "name" in kwargs and kwargs["name"] is not None:
            updates.append("name = ?")
            params.append(kwargs["name"])

        if "category" in kwargs and kwargs["category"] is not None:
            updates.append("category = ?")
            params.append(kwargs["category"])

        if "description" in kwargs and kwargs["description"] is not None:
            updates.append("description = ?")
            params.append(kwargs["description"])

        if "content" in kwargs and kwargs["content"] is not None:
            updates.append("content = ?")
            params.append(json.dumps(kwargs["content"], ensure_ascii=False))

        if "status" in kwargs and kwargs["status"] is not None:
            updates.append("status = ?")
            params.append(kwargs["status"])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.extend([preset_id, project_name])

            sql = f"UPDATE presets SET {', '.join(updates)} WHERE id = ? AND project_name = ?"
            db.execute(sql, tuple(params))

        return self.get_preset(project_name, preset_id)

    def delete_preset(self, project_name: str, preset_id: str) -> bool:
        """删除预设"""
        db = get_presets_db(project_name)
        cursor = db.execute(
            "DELETE FROM presets WHERE id = ? AND project_name = ?",
            (preset_id, project_name),
        )
        return cursor.rowcount > 0

    async def generate_preset(
        self,
        project_name: str,
        description: str,
        category: str = "文风",
    ) -> dict:
        """AI 生成预设"""
        prompt = prompt_templates.render(
            "presets",
            "generate_preset",
            description=description,
            reference="",
        )

        system_prompt = "你是一个专业的写作风格分析师，擅长创建精确的风格预设。请严格按照JSON格式输出。"

        result = await ai_service.generate(prompt, system_prompt)

        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                preset_data = json.loads(json_match.group())
            else:
                preset_data = json.loads(result)
        except:
            preset_data = {
                "name": description[:20],
                "category": category,
                "description": description,
                "style": description,
            }

        return preset_data
