"""
人物卡 API 路由
"""
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from io import BytesIO

from app.services.character_service import CharacterService

api_router = APIRouter(tags=["characters"])
character_service = CharacterService()


class CharacterCreate(BaseModel):
    project_name: str
    name: str
    template_id: Optional[str] = None
    developer_mode: Optional[dict] = None
    player_mode: Optional[dict] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    template_id: Optional[str] = None
    developer_mode: Optional[dict] = None
    player_mode: Optional[dict] = None
    status: Optional[str] = None


class GenerateRequest(BaseModel):
    project_name: str
    concept: str
    character_type: str = "配角"


class BatchGenerateRequest(BaseModel):
    project_name: str
    concepts: list[str]
    character_type: str = "NPC"


# 角色列表
@api_router.get("/characters")
async def list_characters(
    project_name: str = Query(...),
    status: Optional[str] = Query(None),
):
    """获取角色列表"""
    try:
        characters = character_service.list_characters(project_name, status)
        return {"code": 200, "message": "success", "data": characters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/characters")
async def create_character(character: CharacterCreate):
    """创建角色"""
    try:
        result = character_service.create_character(
            project_name=character.project_name,
            name=character.name,
            template_id=character.template_id,
            developer_mode=character.developer_mode,
            player_mode=character.player_mode,
        )
        return {"code": 200, "message": "Character created", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/characters/{character_id}")
async def get_character(character_id: str, project_name: str = Query(...)):
    """获取角色详情"""
    try:
        character = character_service.get_character(project_name, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail="Character not found")
        return {"code": 200, "message": "success", "data": character}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/characters/{character_id}")
async def update_character(character_id: str, project_name: str = Query(...), character: CharacterUpdate = ...):
    """更新角色"""
    try:
        result = character_service.update_character(
            project_name=project_name,
            character_id=character_id,
            **character.model_dump(exclude_unset=True),
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Character not found")
        return {"code": 200, "message": "Character updated", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/characters/{character_id}")
async def delete_character(character_id: str, project_name: str = Query(...)):
    """删除角色"""
    try:
        success = character_service.delete_character(project_name, character_id)
        if not success:
            raise HTTPException(status_code=404, detail="Character not found")
        return {"code": 200, "message": "Character deleted", "data": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 批量操作
@api_router.post("/characters/batch-delete")
async def batch_delete_characters(data: dict):
    """批量删除角色"""
    try:
        ids = data.get("ids", [])
        project_name = data.get("project_name")
        if not ids or not project_name:
            raise HTTPException(status_code=400, detail="Missing ids or project_name")

        deleted = 0
        for char_id in ids:
            if character_service.delete_character(project_name, char_id):
                deleted += 1
        return {"code": 200, "message": f"Deleted {deleted} characters", "data": {"deleted": deleted}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 模板
@api_router.get("/templates")
async def list_templates(project_name: str = Query(None)):
    """获取模板列表"""
    try:
        templates = character_service.list_templates(project_name)
        return {"code": 200, "message": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/templates")
async def create_template(data: dict):
    """创建模板"""
    try:
        result = character_service.create_template(data)
        return {"code": 200, "message": "Template created", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI 生成
@api_router.post("/generate")
async def generate_character(req: GenerateRequest):
    """AI 生成角色"""
    try:
        result = await character_service.generate_character(
            project_name=req.project_name,
            concept=req.concept,
            character_type=req.character_type,
        )
        return {"code": 200, "message": "Generation success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate-batch")
async def generate_characters_batch(req: BatchGenerateRequest):
    """AI 批量生成角色"""
    try:
        results = await character_service.generate_characters_batch(
            project_name=req.project_name,
            concepts=req.concepts,
            character_type=req.character_type,
        )
        return {"code": 200, "message": f"Generated {len(results)} characters", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 导出
@api_router.get("/export/markdown")
async def export_markdown(
    project_name: str = Query(...),
    character_id: Optional[str] = Query(None),
):
    """导出为 Markdown"""
    try:
        if character_id:
            character = character_service.get_character(project_name, character_id)
            if not character:
                raise HTTPException(status_code=404, detail="Character not found")
            characters = [character]
        else:
            characters = character_service.list_characters(project_name)

        md_content = character_service.export_to_markdown(characters)

        return StreamingResponse(
            BytesIO(md_content.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=characters.md"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/json")
async def export_json(
    project_name: str = Query(...),
    character_id: Optional[str] = Query(None),
):
    """导出为 JSON"""
    try:
        if character_id:
            character = character_service.get_character(project_name, character_id)
            if not character:
                raise HTTPException(status_code=404, detail="Character not found")
            characters = [character]
        else:
            characters = character_service.list_characters(project_name)

        json_content = json.dumps(characters, ensure_ascii=False, indent=2)

        return StreamingResponse(
            BytesIO(json_content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=characters.json"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 获取可引用的世界书数据
@api_router.get("/worldbook-context")
async def get_worldbook_context(project_name: str = Query(...)):
    """获取世界书上下文"""
    try:
        context = character_service._get_world_context(project_name)
        return {"code": 200, "message": "success", "data": {"context": context}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
