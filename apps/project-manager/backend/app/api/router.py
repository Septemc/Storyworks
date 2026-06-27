"""
项目管理 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.services.project_service import ProjectService

api_router = APIRouter(tags=["projects"])
project_service = ProjectService()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    genre: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    settings: Optional[dict] = None


@api_router.get("/projects")
async def list_projects():
    """获取项目列表"""
    try:
        projects = project_service.list_projects()
        return {"code": 200, "message": "success", "data": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/projects")
async def create_project(project: ProjectCreate):
    """创建新项目"""
    try:
        result = project_service.create_project(
            name=project.name,
            description=project.description,
            genre=project.genre,
        )
        return {"code": 200, "message": "项目创建成功", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    try:
        project = project_service.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"code": 200, "message": "success", "data": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate):
    """更新项目"""
    try:
        result = project_service.update_project(
            project_id=project_id,
            name=project.name,
            description=project.description,
            genre=project.genre,
            settings=project.settings,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"code": 200, "message": "项目更新成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    try:
        success = project_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"code": 200, "message": "项目删除成功", "data": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/modules")
async def list_modules():
    """获取可用模块列表"""
    modules = [
        {"id": "worldbook", "name": "世界书", "port": 8001, "description": "世界观设定生成器"},
        {"id": "characters", "name": "人物卡", "port": 8002, "description": "角色资料生成器"},
        {"id": "scripts", "name": "剧本", "port": 8003, "description": "剧情结构生成器"},
        {"id": "presets", "name": "预设", "port": 8004, "description": "风格预设生成器"},
    ]
    return {"code": 200, "message": "success", "data": modules}
