import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TEMPLATE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "当前开发现状文档"
    / "角色模板"
    / "默认通用角色模板"
    / "角色模板-默认通用角色模板.json"
)


@lru_cache(maxsize=1)
def load_default_character_template() -> dict[str, Any]:
    return json.loads(DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8-sig"))


class CharacterTemplateService:
    def list_templates(self) -> list[dict[str, Any]]:
        return [load_default_character_template()]

    def get_template(self, template_id: str) -> dict[str, Any]:
        template = load_default_character_template()
        if template["template_id"] != template_id:
            raise KeyError(template_id)
        return template
