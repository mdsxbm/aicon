"""
错误处理中间件 - 统一处理应用异常
"""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.logging import logger
from src.core.exceptions import AICGException


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """错误处理中间件"""
    try:
        response = await call_next(request)
        return response

    except AICGException as exc:
        # 处理自定义异常
        logger.error(
            "AICG应用异常",
            exception_type=type(exc).__name__,
            message=exc.message,
            error_code=exc.error_code,
            status_code=exc.status_code,
            details=exc.details,
            path=request.url.path,
            method=request.method,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": time.time(),
            },
        )

    except Exception as exc:
        # 处理未知异常
        logger.error(
            "未处理的异常",
            exception_type=type(exc).__name__,
            message=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "内部服务器错误" if not settings.DEBUG else str(exc),
                "timestamp": time.time(),
            },
        )


async def not_found_handler(request: Request, call_next: Callable) -> Response:
    """404错误处理中间件"""
    try:
        response = await call_next(request)

        # 如果响应状态码是404，返回自定义404格式
        if response.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": f"路径 {request.url.path} 不存在",
                    "timestamp": time.time(),
                },
            )

        return response

    except Exception as exc:
        # 如果在处理过程中出现异常，由error_handler_middleware处理
        raise exc


async def method_not_allowed_handler(request: Request, call_next: Callable) -> Response:
    """405错误处理中间件"""
    try:
        response = await call_next(request)

        # 如果响应状态码是405，返回自定义405格式
        if response.status_code == 405:
            return JSONResponse(
                status_code=405,
                content={
                    "error": True,
                    "code": "METHOD_NOT_ALLOWED",
                    "message": f"方法 {request.method} 不被允许",
                    "allowed_methods": getattr(response, 'headers', {}).get('allow', ''),
                    "timestamp": time.time(),
                },
            )

        return response

    except Exception as exc:
        raise exc


__all__ = [
    "error_handler_middleware",
    "not_found_handler",
    "method_not_allowed_handler",
]