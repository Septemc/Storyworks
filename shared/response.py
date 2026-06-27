"""
Storyworks 统一响应格式
"""
from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一API响应"""

    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""

    code: int = 400
    message: str = "error"
    error: Optional[str] = None


def success(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "message": message, "data": data}


def error(message: str = "error", code: int = 400, detail: str = None) -> dict:
    """错误响应"""
    return {"code": code, "message": message, "error": detail}
