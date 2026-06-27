"""
世界书 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.services.worldbook_service import WorldbookService

api_router = APIRouter(tags=["worldbook"])
worldbook_service = WorldbookService()


class EntryCreate(BaseModel):
    project_name: str
    category: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[list[str]] = []
    relations: Optional[list[str]] = []
    notes: Optional[str] = None


class EntryUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[list[str]] = None
    relations: Optional[list[str]] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class GenerateRequest(BaseModel):
    project_name: str
    category: str
    title: str
    summary: Optional[str] = None


# 世界书条目
@api_router.get("/entries")
async def list_entries(
    project_name: str = Query(..., description="项目名称"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
):
    """获取世界书条目列表"""
    try:
        entries = worldbook_service.list_entries(project_name, category, status)
        return {"code": 200, "message": "success", "data": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/entries")
async def create_entry(entry: EntryCreate):
    """创建世界书条目"""
    try:
        result = worldbook_service.create_entry(
            project_name=entry.project_name,
            category=entry.category,
            title=entry.title,
            summary=entry.summary,
            content=entry.content,
            keywords=entry.keywords,
            relations=entry.relations,
            notes=entry.notes,
        )
        return {"code": 200, "message": "条目创建成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/entries/{entry_id}")
async def get_entry(entry_id: str, project_name: str = Query(...)):
    """获取条目详情"""
    try:
        entry = worldbook_service.get_entry(project_name, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="条目不存在")
        return {"code": 200, "message": "success", "data": entry}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/entries/{entry_id}")
async def update_entry(entry_id: str, project_name: str = Query(...), entry: EntryUpdate = ...):
    """更新条目"""
    try:
        result = worldbook_service.update_entry(
            project_name=project_name,
            entry_id=entry_id,
            **entry.model_dump(exclude_unset=True),
        )
        if result is None:
            raise HTTPException(status_code=404, detail="条目不存在")
        return {"code": 200, "message": "条目更新成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, project_name: str = Query(...)):
    """删除条目"""
    try:
        success = worldbook_service.delete_entry(project_name, entry_id)
        if not success:
            raise HTTPException(status_code=404, detail="条目不存在")
        return {"code": 200, "message": "条目删除成功", "data": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 世界蓝图
@api_router.get("/blueprints")
async def list_blueprints(project_name: str = Query(...)):
    """获取蓝图列表"""
    try:
        blueprints = worldbook_service.list_blueprints(project_name)
        return {"code": 200, "message": "success", "data": blueprints}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/blueprints")
async def create_blueprint(data: dict):
    """创建蓝图"""
    try:
        result = worldbook_service.create_blueprint(
            project_name=data.get("project_name"),
            name=data.get("name"),
            description=data.get("description"),
            content=data.get("content"),
        )
        return {"code": 200, "message": "蓝图创建成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI 生成
@api_router.post("/generate")
async def generate_entry(req: GenerateRequest):
    """AI 生成世界书条目"""
    try:
        result = await worldbook_service.generate_entry(
            project_name=req.project_name,
            category=req.category,
            title=req.title,
            summary=req.summary,
        )
        return {"code": 200, "message": "生成成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 分类
@api_router.get("/categories")
async def list_categories():
    """获取世界书分类列表"""
    categories = [
        {"id": "history", "name": "历史", "icon": "mdi-history"},
        {"id": "geography", "name": "地理", "icon": "mdi-map"},
        {"id": "politics", "name": "政治", "icon": "mdi-account-group"},
        {"id": "culture", "name": "人文", "icon": "mdi-culture"},
        {"id": "customs", "name": "风俗", "icon": "mdi-hand-heart"},
        {"id": "science", "name": "科学", "icon": "mdi-flask"},
        {"id": "economy", "name": "经济", "icon": "mdi-currency-usd"},
        {"id": "religion", "name": "宗教", "icon": "mdi-church"},
        {"id": "factions", "name": "阵营", "icon": "mdi-flag"},
        {"id": "systems", "name": "制度", "icon": "mdi-sitemap"},
        {"id": "races", "name": "种族", "icon": "mdi-account-multiple"},
        {"id": "languages", "name": "语言", "icon": "mdi-translate"},
        {"id": "tech", "name": "技术体系", "icon": "mdi-cog"},
        {"id": "powers", "name": "能力体系", "icon": "mdi-lightning-bolt"},
        {"id": "laws", "name": "法律", "icon": "mdi-scale-balance"},
        {"id": "organizations", "name": "组织", "icon": "mdi-domain"},
        {"id": "events", "name": "事件", "icon": "mdi-calendar-star"},
        {"id": "landmarks", "name": "地标", "icon": "mdi-map-marker"},
        {"id": "terms", "name": "术语", "icon": "mdi-book-open-page-variant"},
    ]
    return {"code": 200, "message": "success", "data": categories}
