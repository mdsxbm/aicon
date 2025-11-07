"""
API v1 模块
"""

from fastapi import APIRouter

# 创建主路由器
api_router = APIRouter()


@api_router.get("/")
async def api_v1_info():
    """API v1 信息"""
    return {
        "name": "AICG内容分发平台 API v1",
        "version": "1.0.0",
        "status": "under_development",
        "message": "API v1 正在开发中",
    }


# 导入认证相关路由
from .auth import router as auth_router

# 注册路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])

__all__ = ["api_router"]
