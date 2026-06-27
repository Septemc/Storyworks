"""
AI Prompt 模板管理
"""
from pathlib import Path
from typing import Optional


class PromptTemplate:
    """Prompt模板管理器"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # shared/prompts.py -> Storyworks/templates
            template_dir = str(Path(__file__).parent.parent / "templates")
        self.template_dir = Path(template_dir)

    def get_template(self, module: str, template_name: str) -> Optional[str]:
        """获取模板内容"""
        template_path = self.template_dir / module / f"{template_name}.md"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        return None

    def render(self, module: str, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.get_template(module, template_name)
        if template is None:
            raise FileNotFoundError(f"Template not found: {module}/{template_name}")

        # 简单的字符串替换
        for key, value in kwargs.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    def list_templates(self, module: str) -> list[str]:
        """列出模块的所有模板"""
        module_dir = self.template_dir / module
        if not module_dir.exists():
            return []
        return [f.stem for f in module_dir.glob("*.md")]


# 单例
prompt_templates = PromptTemplate()
