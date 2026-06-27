"""
预设 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.services.preset_service import PresetService

api_router = APIRouter(tags=["presets"])
preset_service = PresetService()


class PresetCreate(BaseModel):
    project_name: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[dict] = None


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[dict] = None
    status: Optional[str] = None


class GenerateRequest(BaseModel):
    project_name: str
    description: str
    category: str = "文风"


@api_router.get("/presets")
async def list_presets(
    project_name: str = Query(...),
    category: Optional[str] = Query(None),
):
    """获取预设列表"""
    try:
        presets = preset_service.list_presets(project_name, category)
        return {"code": 200, "message": "success", "data": presets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/presets")
async def create_preset(preset: PresetCreate):
    """创建预设"""
    try:
        result = preset_service.create_preset(
            project_name=preset.project_name,
            name=preset.name,
            category=preset.category,
            description=preset.description,
            content=preset.content,
        )
        return {"code": 200, "message": "预设创建成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/presets/{preset_id}")
async def get_preset(preset_id: str, project_name: str = Query(...)):
    """获取预设详情"""
    try:
        preset = preset_service.get_preset(project_name, preset_id)
        if preset is None:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {"code": 200, "message": "success", "data": preset}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/presets/{preset_id}")
async def update_preset(preset_id: str, project_name: str = Query(...), preset: PresetUpdate = ...):
    """更新预设"""
    try:
        result = preset_service.update_preset(
            project_name=project_name,
            preset_id=preset_id,
            **preset.model_dump(exclude_unset=True),
        )
        if result is None:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {"code": 200, "message": "预设更新成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: str, project_name: str = Query(...)):
    """删除预设"""
    try:
        success = preset_service.delete_preset(project_name, preset_id)
        if not success:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {"code": 200, "message": "预设删除成功", "data": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate")
async def generate_preset(req: GenerateRequest):
    """AI 生成预设"""
    try:
        result = await preset_service.generate_preset(
            project_name=req.project_name,
            description=req.description,
            category=req.category,
        )
        return {"code": 200, "message": "生成成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/categories")
async def list_categories():
    """获取预设分类"""
    categories = [
        {"id": "style", "name": "文风"},
        {"id": "genre", "name": "题材"},
        {"id": "plot", "name": "剧情偏好"},
        {"id": "character", "name": "人物塑造"},
        {"id": "quality", "name": "质量"},
        {"id": "format", "name": "输出格式"},
    ]
    return {"code": 200, "message": "success", "data": categories}
