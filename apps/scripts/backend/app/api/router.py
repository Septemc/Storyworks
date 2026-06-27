"""
剧本 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.services.script_service import ScriptService

api_router = APIRouter(tags=["scripts"])
script_service = ScriptService()


class ScriptCreate(BaseModel):
    project_name: str
    title: str
    type: str = "outline"  # outline/act/chapter/scene
    parent_id: Optional[str] = None
    content: Optional[dict] = None
    constraints: Optional[dict] = None


class ScriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[dict] = None
    constraints: Optional[dict] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class GenerateRequest(BaseModel):
    project_name: str
    concept: str
    genre: str = "奇幻"


@api_router.get("/scripts")
async def list_scripts(
    project_name: str = Query(...),
    type: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
):
    """获取剧本列表"""
    try:
        scripts = script_service.list_scripts(project_name, type, parent_id)
        return {"code": 200, "message": "success", "data": scripts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/scripts")
async def create_script(script: ScriptCreate):
    """创建剧本"""
    try:
        result = script_service.create_script(
            project_name=script.project_name,
            title=script.title,
            type=script.type,
            parent_id=script.parent_id,
            content=script.content,
            constraints=script.constraints,
        )
        return {"code": 200, "message": "剧本创建成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scripts/{script_id}")
async def get_script(script_id: str, project_name: str = Query(...)):
    """获取剧本详情"""
    try:
        script = script_service.get_script(project_name, script_id)
        if script is None:
            raise HTTPException(status_code=404, detail="剧本不存在")
        return {"code": 200, "message": "success", "data": script}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/scripts/{script_id}")
async def update_script(script_id: str, project_name: str = Query(...), script: ScriptUpdate = ...):
    """更新剧本"""
    try:
        result = script_service.update_script(
            project_name=project_name,
            script_id=script_id,
            **script.model_dump(exclude_unset=True),
        )
        if result is None:
            raise HTTPException(status_code=404, detail="剧本不存在")
        return {"code": 200, "message": "剧本更新成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/scripts/{script_id}")
async def delete_script(script_id: str, project_name: str = Query(...)):
    """删除剧本"""
    try:
        success = script_service.delete_script(project_name, script_id)
        if not success:
            raise HTTPException(status_code=404, detail="剧本不存在")
        return {"code": 200, "message": "剧本删除成功", "data": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scripts/{script_id}/children")
async def get_script_children(script_id: str, project_name: str = Query(...)):
    """获取子剧本"""
    try:
        children = script_service.get_children(project_name, script_id)
        return {"code": 200, "message": "success", "data": children}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scripts/tree")
async def get_script_tree(project_name: str = Query(...)):
    """获取剧本树结构"""
    try:
        tree = script_service.get_script_tree(project_name)
        return {"code": 200, "message": "success", "data": tree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate")
async def generate_script(req: GenerateRequest):
    """AI 生成剧本"""
    try:
        result = await script_service.generate_script(
            project_name=req.project_name,
            concept=req.concept,
            genre=req.genre,
        )
        return {"code": 200, "message": "生成成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
