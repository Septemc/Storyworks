from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from .database import (
    init_database,
    parse_json,
    record_version,
)
from .routers.ai import router as ai_router
from .routers.characters import router as characters_router
from .routers.presets import router as presets_router
from .routers.projects import router as projects_router
from .routers.scripts import router as scripts_router
from .routers.system import router as system_router
from .routers.versions import router as versions_router
from .routers.worldbook import router as worldbook_router
from .services.ai_service import (
    clean_text,
    record_ai_operation,
)
from .services.character_service import (
    build_character_graph as service_build_character_graph,
    create_character_payload as service_create_character,
    create_character_relation_payload as service_create_character_relation,
    delete_character_payload as service_delete_character,
    delete_character_relation_payload as service_delete_character_relation,
    ensure_character as service_ensure_character,
    export_characters as service_export_characters,
    get_character as service_get_character,
    get_character_detail as service_get_character_detail,
    list_character_relations as service_list_character_relations,
    list_characters as service_list_characters,
    update_character_payload as service_update_character,
)
from .services.preset_service import (
    apply_preset_payload as service_apply_preset,
    combine_presets_payload as service_combine_presets,
    create_preset_payload as service_create_preset,
    delete_preset_payload as service_delete_preset,
    ensure_preset as service_ensure_preset,
    export_presets as service_export_presets,
    get_preset as service_get_preset,
    list_presets as service_list_presets,
    update_preset_payload as service_update_preset,
)
from .services.character_schema import normalize_character_contract
from .services.script_service import (
    add_script_reference_payload as service_add_script_reference,
    build_script_tree as service_build_script_tree,
    create_script_payload as service_create_script,
    delete_script_payload as service_delete_script,
    delete_script_reference_payload as service_delete_script_reference,
    ensure_script as service_ensure_script,
    export_scripts as service_export_scripts,
    get_script as service_get_script,
    get_script_detail as service_get_script_detail,
    list_scripts as service_list_scripts,
    referenced_by as service_referenced_by,
    update_script_payload as service_update_script,
)
from .services.version_service import (
    list_versions as service_list_versions,
    restore_version_payload as service_restore_version,
    version_diff_payload as service_version_diff,
)
from .services.worldbook_service import (
    build_worldbook_graph as service_build_worldbook_graph,
    create_worldbook_entry_payload as service_create_worldbook_entry,
    create_worldbook_relation_payload as service_create_worldbook_relation,
    delete_worldbook_entry_payload as service_delete_worldbook_entry,
    delete_worldbook_relation_payload as service_delete_worldbook_relation,
    ensure_worldbook_entry as service_ensure_worldbook_entry,
    export_worldbook as service_export_worldbook,
    get_worldbook_entry as service_get_worldbook_entry,
    get_worldbook_entry_detail as service_get_worldbook_entry_detail,
    list_worldbook_categories,
    list_worldbook_entries,
    list_worldbook_relations,
    update_worldbook_entry_payload as service_update_worldbook_entry,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    yield


app = FastAPI(title="Storyworks Unified API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(system_router)
app.include_router(ai_router)
app.include_router(projects_router)
app.include_router(worldbook_router)
app.include_router(scripts_router)
app.include_router(characters_router)
app.include_router(presets_router)
app.include_router(versions_router)


def ok(data: Any = None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


def parse_row(row: Optional[dict], fields: dict[str, Any]) -> Optional[dict]:
    if not row:
        return None
    for key, default in fields.items():
        row[key] = parse_json(row.get(key), default)
    return row


def ensure_character_gender_field(row: Optional[dict]) -> Optional[dict]:
    return normalize_character_contract(row)


def require_row(row: Optional[dict], message: str):
    if row is None:
        raise HTTPException(status_code=404, detail=message)
    return row


def list_categories(project_id: str):
    return list_worldbook_categories(project_id)


def get_worldbook_entry(project_id: str, entry_id: str):
    return service_get_worldbook_entry(project_id, entry_id)


def get_character(project_id: str, character_id: str):
    return service_get_character(project_id, character_id)


def get_script(project_id: str, script_id: str):
    return service_get_script(project_id, script_id)


def get_preset(project_id: str, preset_id: str):
    return service_get_preset(project_id, preset_id)


def ensure_world_entry(project_id: str, entry_id: str):
    return service_ensure_worldbook_entry(project_id, entry_id)


def ensure_character(project_id: str, character_id: str):
    return service_ensure_character(project_id, character_id)


def ensure_script(project_id: str, script_id: str):
    return service_ensure_script(project_id, script_id)


def build_script_tree(project_id: str):
    return service_build_script_tree(project_id)


def create_version_snapshot(project_id: str, entity_type: str, entity_id: str, row: dict, summary: str = ""):
    version = int(row.get("version") or 1)
    record_version(project_id, entity_type, entity_id, version, row, summary)


def record_ai_apply_metadata(project_id: str, target_type: str, target_id: str, data: dict, applied_result: Any):
    meta = data.get("ai_apply")
    if not isinstance(meta, dict):
        return
    record_ai_operation(
        project_id,
        target_type,
        "apply",
        str(meta.get("prompt") or ""),
        meta.get("result", applied_result),
        target_id=target_id,
        section=clean_text(meta.get("section")),
        field=clean_text(meta.get("field")),
        instruction=clean_text(meta.get("instruction")),
        request=meta.get("request") if isinstance(meta.get("request"), dict) else {},
        process_log=meta.get("process_log") if isinstance(meta.get("process_log"), list) else [],
    )


def ai_update_summary(data: dict, fallback: str) -> str:
    if data.get("_version_summary"):
        return str(data.get("_version_summary"))
    if data.get("summary"):
        return str(data.get("summary"))
    meta = data.get("ai_apply")
    if isinstance(meta, dict):
        target = " / ".join(item for item in [clean_text(meta.get("section")), clean_text(meta.get("field"))] if item)
        return f"AI迭代 {target or '全文'}"
    return fallback



def worldbook_entries(project_id: str, category_id: Optional[str] = None, status: Optional[str] = None, q: str = "", tag: str = "", min_importance: int = 1):
    return ok(list_worldbook_entries(project_id, category_id=category_id, status=status, q=q, tag=tag, min_importance=min_importance))


def create_worldbook_entry(project_id: str, data: dict = Body(...)):
    return ok(service_create_worldbook_entry(project_id, data), "条目创建成功")


def worldbook_entry(project_id: str, entry_id: str):
    return ok(service_get_worldbook_entry_detail(project_id, entry_id))


def update_worldbook_entry(project_id: str, entry_id: str, data: dict = Body(...)):
    return ok(service_update_worldbook_entry(project_id, entry_id, data), "条目更新成功")


def delete_worldbook_entry(project_id: str, entry_id: str):
    service_delete_worldbook_entry(project_id, entry_id)
    return ok(None, "条目删除成功")


def worldbook_relations(project_id: str):
    return ok(list_worldbook_relations(project_id))


def create_worldbook_relation(project_id: str, data: dict = Body(...)):
    return ok(service_create_worldbook_relation(project_id, data), "关联创建成功")


def delete_worldbook_relation(project_id: str, relation_id: str):
    service_delete_worldbook_relation(project_id, relation_id)
    return ok(None, "关联删除成功")


def worldbook_graph(project_id: str, category_id: Optional[str] = None, min_importance: int = 1):
    return ok(service_build_worldbook_graph(project_id, category_id=category_id, min_importance=min_importance))


def export_worldbook(project_id: str, format: str = "markdown", ids: str = ""):
    return ok(service_export_worldbook(project_id, format, ids))



def characters(project_id: str, q: str = "", character_type: str = "", status: str = "", tag: str = ""):
    return ok(service_list_characters(project_id, q=q, character_type=character_type, status=status, tag=tag))


def create_character(project_id: str, data: dict = Body(...)):
    return ok(service_create_character(project_id, data), "角色创建成功")


def character(project_id: str, character_id: str):
    return ok(service_get_character_detail(project_id, character_id))


def update_character(project_id: str, character_id: str, data: dict = Body(...)):
    return ok(service_update_character(project_id, character_id, data), "角色更新成功")


def delete_character(project_id: str, character_id: str):
    service_delete_character(project_id, character_id)
    return ok(None, "角色删除成功")


def character_relations(project_id: str):
    return ok(service_list_character_relations(project_id))


def create_character_relation(project_id: str, data: dict = Body(...)):
    return ok(service_create_character_relation(project_id, data), "关系创建成功")


def delete_character_relation(project_id: str, relation_id: str):
    service_delete_character_relation(project_id, relation_id)
    return ok(None, "关系删除成功")


def character_graph(project_id: str):
    return ok(service_build_character_graph(project_id))



def export_characters(project_id: str, format: str = "markdown", ids: str = ""):
    return ok(service_export_characters(project_id, format, ids))


def scripts(project_id: str, node_type: str = "", status: str = "", q: str = ""):
    return ok(service_list_scripts(project_id, node_type=node_type, status=status, q=q))


def script_tree(project_id: str):
    return ok(service_build_script_tree(project_id))


def create_script(project_id: str, data: dict = Body(...)):
    return ok(service_create_script(project_id, data), "节点创建成功")


def script(project_id: str, script_id: str):
    return ok(service_get_script_detail(project_id, script_id))


def update_script(project_id: str, script_id: str, data: dict = Body(...)):
    return ok(service_update_script(project_id, script_id, data), "节点更新成功")


def delete_script(project_id: str, script_id: str):
    service_delete_script(project_id, script_id)
    return ok(None, "节点删除成功")


def add_script_reference(project_id: str, script_id: str, data: dict = Body(...)):
    return ok(service_add_script_reference(project_id, script_id, data), "引用已添加")


def delete_script_reference(project_id: str, reference_id: str):
    service_delete_script_reference(project_id, reference_id)
    return ok(None, "引用已删除")


def referenced_by(project_id: str, ref_type: str, ref_id: str):
    return ok(service_referenced_by(project_id, ref_type, ref_id))



def export_scripts(project_id: str, format: str = "markdown"):
    return ok(service_export_scripts(project_id, format))


def presets(project_id: str, category: str = "", q: str = ""):
    return ok(service_list_presets(project_id, category=category, q=q))


def create_preset(project_id: str, data: dict = Body(...)):
    return ok(service_create_preset(project_id, data), "预设创建成功")


def preset(project_id: str, preset_id: str):
    return ok(service_ensure_preset(project_id, preset_id))


def update_preset(project_id: str, preset_id: str, data: dict = Body(...)):
    return ok(service_update_preset(project_id, preset_id, data), "预设更新成功")


def delete_preset(project_id: str, preset_id: str):
    service_delete_preset(project_id, preset_id)
    return ok(None, "预设删除成功")



def apply_preset(project_id: str, data: dict = Body(...)):
    return ok(service_apply_preset(project_id, data), "预设已应用")


def combine_presets(project_id: str, data: dict = Body(...)):
    return ok(service_combine_presets(project_id, data), "预设组合完成")


def export_presets(project_id: str, format: str = "json"):
    return ok(service_export_presets(project_id, format))


def versions(project_id: str, entity_type: str, entity_id: str):
    return ok(service_list_versions(project_id, entity_type, entity_id))


def version_diff(project_id: str, version_id: str):
    return ok(service_version_diff(project_id, version_id), "版本差异已生成")


def restore_version(project_id: str, version_id: str):
    return ok(service_restore_version(project_id, version_id), "版本已恢复")
