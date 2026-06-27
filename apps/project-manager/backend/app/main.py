"""
Storyworks 项目管理应用 - FastAPI 入口
"""
import sys
from pathlib import Path

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.router import api_router
from app.core.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    init_database()
    yield


app = FastAPI(
    title="Storyworks 项目管理",
    description="Storyworks 项目管理应用 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Storyworks 项目管理服务", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
