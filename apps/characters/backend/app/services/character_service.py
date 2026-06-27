"""
人物卡业务逻辑
"""
import json
from typing import Optional
from datetime import datetime

from shared.database import generate_id
from shared.ai_service import ai_service
from shared.prompts import prompt_templates
from app.core.database import get_characters_db


class CharacterService:
    """人物卡服务"""

    def list_characters(
        self,
        project_name: str,
        status: Optional[str] = None,
    ) -> list[dict]:
        """获取角色列表"""
        db = get_characters_db(project_name)

        sql = "SELECT * FROM characters WHERE project_name = ?"
        params = [project_name]

        if status:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY updated_at DESC"

        characters = db.fetch_all(sql, tuple(params))

        # 解析 JSON 字段
        for char in characters:
            char["developer_mode"] = json.loads(char.get("developer_mode") or "{}")
            char["player_mode"] = json.loads(char.get("player_mode") or "{}")

        return characters

    def get_character(self, project_name: str, character_id: str) -> Optional[dict]:
        """获取角色详情"""
        db = get_characters_db(project_name)
        character = db.fetch_one(
            "SELECT * FROM characters WHERE id = ? AND project_name = ?",
            (character_id, project_name),
        )
        if character:
            character["developer_mode"] = json.loads(character.get("developer_mode") or "{}")
            character["player_mode"] = json.loads(character.get("player_mode") or "{}")
        return character

    def create_character(
        self,
        project_name: str,
        name: str,
        template_id: str = None,
        developer_mode: dict = None,
        player_mode: dict = None,
    ) -> dict:
        """创建角色"""
        db = get_characters_db(project_name)
        char_id = generate_id("char")
        now = datetime.now().isoformat()

        db.execute(
            """INSERT INTO characters
               (id, project_name, template_id, name, developer_mode, player_mode, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                char_id,
                project_name,
                template_id,
                name,
                json.dumps(developer_mode or {}, ensure_ascii=False),
                json.dumps(player_mode or {}, ensure_ascii=False),
                "draft",
                now,
                now,
            ),
        )

        return self.get_character(project_name, char_id)

    def update_character(
        self,
        project_name: str,
        character_id: str,
        **kwargs,
    ) -> Optional[dict]:
        """更新角色"""
        db = get_characters_db(project_name)

        existing = db.fetch_one(
            "SELECT id FROM characters WHERE id = ? AND project_name = ?",
            (character_id, project_name),
        )
        if not existing:
            return None

        updates = []
        params = []

        if "name" in kwargs and kwargs["name"] is not None:
            updates.append("name = ?")
            params.append(kwargs["name"])

        if "template_id" in kwargs and kwargs["template_id"] is not None:
            updates.append("template_id = ?")
            params.append(kwargs["template_id"])

        if "developer_mode" in kwargs and kwargs["developer_mode"] is not None:
            updates.append("developer_mode = ?")
            params.append(json.dumps(kwargs["developer_mode"], ensure_ascii=False))

        if "player_mode" in kwargs and kwargs["player_mode"] is not None:
            updates.append("player_mode = ?")
            params.append(json.dumps(kwargs["player_mode"], ensure_ascii=False))

        if "status" in kwargs and kwargs["status"] is not None:
            updates.append("status = ?")
            params.append(kwargs["status"])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.extend([character_id, project_name])

            sql = f"UPDATE characters SET {', '.join(updates)} WHERE id = ? AND project_name = ?"
            db.execute(sql, tuple(params))

        return self.get_character(project_name, character_id)

    def delete_character(self, project_name: str, character_id: str) -> bool:
        """删除角色"""
        db = get_characters_db(project_name)
        cursor = db.execute(
            "DELETE FROM characters WHERE id = ? AND project_name = ?",
            (character_id, project_name),
        )
        return cursor.rowcount > 0

    def list_templates(self, project_name: str = None) -> list[dict]:
        """获取模板列表"""
        # 内置模板
        builtin_templates = [
            {
                "id": "default",
                "name": "默认通用模板",
                "description": "包含基础信息、见闻设定、秘密过往、数值属性、人际关系、装备物品、技能功法、命运机缘",
                "is_builtin": True,
            },
            {
                "id": "simple",
                "name": "简洁模板",
                "description": "只包含基础信息和性格特征",
                "is_builtin": True,
            },
        ]

        # 项目自定义模板
        if project_name:
            db = get_characters_db(project_name)
            custom = db.fetch_all(
                "SELECT * FROM character_templates WHERE is_builtin = FALSE"
            )
            return builtin_templates + custom

        return builtin_templates

    def create_template(self, data: dict) -> dict:
        """创建模板"""
        # 暂不实现项目模板创建
        raise NotImplementedError("自定义模板功能待实现")

    async def generate_character(
        self,
        project_name: str,
        concept: str,
        character_type: str = "配角",
    ) -> dict:
        """AI 生成角色"""
        # 获取世界书上下文
        world_context = self._get_world_context(project_name)

        # 渲染 Prompt
        prompt = prompt_templates.render(
            "characters",
            "generate_character",
            concept=concept,
            character_type=character_type,
            world_context=world_context or "暂无世界背景",
            preset="暂无风格预设",
        )

        system_prompt = "你是一个专业的角色设计助手，擅长创建立体、有深度的角色。请严格按照JSON格式输出。"

        # 调用 AI
        result = await ai_service.generate(prompt, system_prompt)

        # 解析 JSON
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                character_data = json.loads(json_match.group())
            else:
                character_data = json.loads(result)
        except:
            # 解析失败，返回原始文本
            character_data = {
                "developer_mode": {
                    "basic": {"name": concept, "summary": result[:200]},
                    "knowledge": {"background": result},
                },
                "player_mode": {
                    "basic": {"name": concept, "summary": "见 developer_mode"},
                },
            }

        return character_data

    def _get_world_context(self, project_name: str) -> str:
        """获取世界书上下文"""
        try:
            from shared.database import read_other_module_data

            entries = read_other_module_data(
                project_name,
                "worldbook",
                "worldbook.db",
                "SELECT title, summary FROM worldbook_entries WHERE project_name = ? LIMIT 5",
                (project_name,),
            )

            if not entries:
                return ""

            context = "世界背景参考：\n"
            for entry in entries:
                context += f"- {entry['title']}: {entry.get('summary', '')}\n"
            return context
        except:
            return ""

    async def generate_characters_batch(
        self,
        project_name: str,
        concepts: list[str],
        character_type: str = "NPC",
    ) -> list[dict]:
        """AI 批量生成角色"""
        results = []
        for concept in concepts:
            try:
                result = await self.generate_character(project_name, concept, character_type)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "concept": concept})
        return results

    def export_to_markdown(self, characters: list[dict]) -> str:
        """导出角色为 Markdown 格式"""
        lines = ["# 角色列表\n"]

        for char in characters:
            lines.append(f"## {char.get('name', 'Unknown')}\n")

            dev_mode = char.get("developer_mode", {})

            # 基础信息
            basic = dev_mode.get("basic", {})
            if basic:
                lines.append("### 基础信息\n")
                for key, value in basic.items():
                    if value:
                        label = self._get_field_label(key)
                        lines.append(f"- **{label}**: {value}")
                lines.append("")

            # 见闻设定
            knowledge = dev_mode.get("knowledge", {})
            if knowledge:
                lines.append("### 见闻设定\n")
                for key, value in knowledge.items():
                    if value:
                        label = self._get_field_label(key)
                        lines.append(f"- **{label}**: {value}")
                lines.append("")

            # 秘密过往
            secrets = dev_mode.get("secrets", {})
            if secrets:
                lines.append("### 秘密过往\n")
                for key, value in secrets.items():
                    if value:
                        label = self._get_field_label(key)
                        lines.append(f"- **{label}**: {value}")
                lines.append("")

            # 数值属性
            attributes = dev_mode.get("attributes", {})
            if attributes:
                lines.append("### 数值属性\n")
                for key, value in attributes.items():
                    if value:
                        label = self._get_field_label(key)
                        lines.append(f"- **{label}**: {value}")
                lines.append("")

            # 人际关系
            relations = dev_mode.get("relations", [])
            if relations:
                lines.append("### 人际关系\n")
                for rel in relations:
                    if isinstance(rel, dict):
                        target = rel.get("target", "")
                        rel_type = rel.get("type", "")
                        desc = rel.get("description", "")
                        lines.append(f"- **{target}** ({rel_type}): {desc}")
                    else:
                        lines.append(f"- {rel}")
                lines.append("")

            # 装备物品
            inventory = dev_mode.get("inventory", [])
            if inventory:
                lines.append("### 装备物品\n")
                for item in inventory:
                    if isinstance(item, dict):
                        name = item.get("name", "")
                        item_type = item.get("type", "")
                        desc = item.get("description", "")
                        lines.append(f"- **{name}** ({item_type}): {desc}")
                    else:
                        lines.append(f"- {item}")
                lines.append("")

            # 技能功法
            skills = dev_mode.get("skills", [])
            if skills:
                lines.append("### 技能功法\n")
                for skill in skills:
                    if isinstance(skill, dict):
                        name = skill.get("name", "")
                        level = skill.get("level", "")
                        desc = skill.get("description", "")
                        lines.append(f"- **{name}** (等级: {level}): {desc}")
                    else:
                        lines.append(f"- {skill}")
                lines.append("")

            # 命运机缘
            fortune = dev_mode.get("fortune", {})
            if fortune:
                lines.append("### 命运机缘\n")
                destiny_tags = fortune.get("destiny_tags", [])
                if destiny_tags:
                    lines.append(f"- **天命标签**: {', '.join(destiny_tags)}")
                causal_hints = fortune.get("causal_hints", [])
                if causal_hints:
                    lines.append(f"- **因果提示**: {', '.join(causal_hints)}")
                lines.append("")

            lines.append("---\n")

        return "\n".join(lines)

    def _get_field_label(self, key: str) -> str:
        """获取字段标签"""
        labels = {
            "name": "姓名",
            "identity": "身份",
            "level": "等级/修为",
            "summary": "简介",
            "personality": "性格",
            "appearance": "外貌",
            "background": "背景",
            "motivation": "动机",
            "trauma": "心理创伤",
            "hidden_identity": "隐藏身份",
            "secret": "秘密",
            "health": "健康状态",
            "special": "特殊状态",
        }
        return labels.get(key, key)
