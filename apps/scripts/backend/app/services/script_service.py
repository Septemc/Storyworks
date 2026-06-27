"""
剧本业务逻辑
"""
import json
from typing import Optional
from datetime import datetime

from shared.database import generate_id
from shared.ai_service import ai_service
from shared.prompts import prompt_templates
from app.core.database import get_scripts_db


class ScriptService:
    """剧本服务"""

    def list_scripts(
        self,
        project_name: str,
        type: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> list[dict]:
        """获取剧本列表"""
        db = get_scripts_db(project_name)

        sql = "SELECT * FROM scripts WHERE project_name = ?"
        params = [project_name]

        if type:
            sql += " AND type = ?"
            params.append(type)

        if parent_id:
            sql += " AND parent_id = ?"
            params.append(parent_id)
        else:
            sql += " AND parent_id IS NULL"

        sql += " ORDER BY sort_order, created_at"

        scripts = db.fetch_all(sql, tuple(params))

        for script in scripts:
            script["content"] = json.loads(script.get("content") or "{}")
            script["constraints"] = json.loads(script.get("constraints") or "{}")

        return scripts

    def get_script(self, project_name: str, script_id: str) -> Optional[dict]:
        """获取剧本详情"""
        db = get_scripts_db(project_name)
        script = db.fetch_one(
            "SELECT * FROM scripts WHERE id = ? AND project_name = ?",
            (script_id, project_name),
        )
        if script:
            script["content"] = json.loads(script.get("content") or "{}")
            script["constraints"] = json.loads(script.get("constraints") or "{}")
        return script

    def create_script(
        self,
        project_name: str,
        title: str,
        type: str = "outline",
        parent_id: str = None,
        content: dict = None,
        constraints: dict = None,
    ) -> dict:
        """创建剧本"""
        db = get_scripts_db(project_name)
        script_id = generate_id("scr")
        now = datetime.now().isoformat()

        db.execute(
            """INSERT INTO scripts
               (id, project_name, title, type, parent_id, content, constraints, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                script_id,
                project_name,
                title,
                type,
                parent_id,
                json.dumps(content or {}, ensure_ascii=False),
                json.dumps(constraints or {}, ensure_ascii=False),
                "draft",
                now,
                now,
            ),
        )

        return self.get_script(project_name, script_id)

    def update_script(
        self,
        project_name: str,
        script_id: str,
        **kwargs,
    ) -> Optional[dict]:
        """更新剧本"""
        db = get_scripts_db(project_name)

        existing = db.fetch_one(
            "SELECT id FROM scripts WHERE id = ? AND project_name = ?",
            (script_id, project_name),
        )
        if not existing:
            return None

        updates = []
        params = []

        if "title" in kwargs and kwargs["title"] is not None:
            updates.append("title = ?")
            params.append(kwargs["title"])

        if "content" in kwargs and kwargs["content"] is not None:
            updates.append("content = ?")
            params.append(json.dumps(kwargs["content"], ensure_ascii=False))

        if "constraints" in kwargs and kwargs["constraints"] is not None:
            updates.append("constraints = ?")
            params.append(json.dumps(kwargs["constraints"], ensure_ascii=False))

        if "status" in kwargs and kwargs["status"] is not None:
            updates.append("status = ?")
            params.append(kwargs["status"])

        if "sort_order" in kwargs and kwargs["sort_order"] is not None:
            updates.append("sort_order = ?")
            params.append(kwargs["sort_order"])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.extend([script_id, project_name])

            sql = f"UPDATE scripts SET {', '.join(updates)} WHERE id = ? AND project_name = ?"
            db.execute(sql, tuple(params))

        return self.get_script(project_name, script_id)

    def delete_script(self, project_name: str, script_id: str) -> bool:
        """删除剧本"""
        db = get_scripts_db(project_name)

        # 递归删除子剧本
        children = db.fetch_all(
            "SELECT id FROM scripts WHERE parent_id = ? AND project_name = ?",
            (script_id, project_name),
        )
        for child in children:
            self.delete_script(project_name, child["id"])

        cursor = db.execute(
            "DELETE FROM scripts WHERE id = ? AND project_name = ?",
            (script_id, project_name),
        )
        return cursor.rowcount > 0

    def get_children(self, project_name: str, parent_id: str) -> list[dict]:
        """获取子剧本"""
        db = get_scripts_db(project_name)
        children = db.fetch_all(
            "SELECT * FROM scripts WHERE parent_id = ? AND project_name = ? ORDER BY sort_order",
            (parent_id, project_name),
        )
        for child in children:
            child["content"] = json.loads(child.get("content") or "{}")
            child["constraints"] = json.loads(child.get("constraints") or "{}")
        return children

    def get_script_tree(self, project_name: str) -> list[dict]:
        """获取剧本树结构"""
        db = get_scripts_db(project_name)

        # 获取所有顶层剧本
        root_scripts = db.fetch_all(
            """SELECT * FROM scripts
               WHERE project_name = ? AND parent_id IS NULL
               ORDER BY sort_order, created_at""",
            (project_name,),
        )

        def build_tree(parent):
            parent["content"] = json.loads(parent.get("content") or "{}")
            parent["constraints"] = json.loads(parent.get("constraints") or "{}")

            children = db.fetch_all(
                "SELECT * FROM scripts WHERE parent_id = ? ORDER BY sort_order",
                (parent["id"],),
            )
            parent["children"] = [build_tree(child) for child in children]
            return parent

        return [build_tree(script) for script in root_scripts]

    async def generate_script(
        self,
        project_name: str,
        concept: str,
        genre: str = "奇幻",
    ) -> dict:
        """AI 生成剧本"""
        # 获取世界书和角色上下文
        world_context = self._get_world_context(project_name)
        characters = self._get_characters(project_name)

        # 渲染 Prompt
        prompt = prompt_templates.render(
            "scripts",
            "generate_outline",
            concept=concept,
            genre=genre,
            world_context=world_context or "暂无世界背景",
            characters=characters or "暂无角色信息",
        )

        system_prompt = "你是一个专业的剧本策划助手，擅长构建引人入胜的故事结构。请严格按照JSON格式输出。"

        # 调用 AI
        result = await ai_service.generate(prompt, system_prompt)

        # 解析 JSON
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                script_data = json.loads(json_match.group())
            else:
                script_data = json.loads(result)
        except:
            script_data = {
                "title": concept,
                "genre": genre,
                "summary": result[:500],
            }

        return script_data

    def _get_world_context(self, project_name: str) -> str:
        """获取世界书上下文"""
        try:
            from shared.database import read_other_module_data
            entries = read_other_module_data(
                project_name, "worldbook", "worldbook.db",
                "SELECT title, summary FROM worldbook_entries WHERE project_name = ? LIMIT 5",
                (project_name,),
            )
            if not entries:
                return ""
            context = "世界背景：\n"
            for entry in entries:
                context += f"- {entry['title']}: {entry.get('summary', '')}\n"
            return context
        except:
            return ""

    def _get_characters(self, project_name: str) -> str:
        """获取角色信息"""
        try:
            from shared.database import read_other_module_data
            characters = read_other_module_data(
                project_name, "characters", "characters.db",
                "SELECT name, developer_mode FROM characters WHERE project_name = ? LIMIT 5",
                (project_name,),
            )
            if not characters:
                return ""
            result = "主要角色：\n"
            for char in characters:
                dev_mode = json.loads(char.get("developer_mode") or "{}")
                summary = dev_mode.get("basic", {}).get("summary", "")
                result += f"- {char['name']}: {summary}\n"
            return result
        except:
            return ""
