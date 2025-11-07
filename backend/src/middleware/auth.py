"""
认证中间件 - 处理用户认证和授权
"""

from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from src.core.logging import logger
from src.core.security import TokenError, verify_token


async def auth_middleware(request: Request, call_next: Callable) -> Response:
    """
    认证中间件 - 验证JWT Token
    注意：此中间件为可选实现，具体认证应在路由级别通过Depends处理
    """
    # 获取Authorization头
    authorization = request.headers.get("Authorization")

    # 如果没有Authorization头，继续处理（允许匿名访问）
    if not authorization:
        return await call_next(request)

    # 检查Bearer token格式
    if not authorization.startswith("Bearer "):
        logger.warning("无效的Authorization头格式", path=request.url.path)
        return await call_next(request)

    token = authorization.split(" ")[1]

    try:
        # 验证token
        payload = verify_token(token)

        # 将用户信息添加到request state
        request.state.user_id = payload.get("sub")
        request.state.username = payload.get("username")

        logger.debug(
            "用户认证成功",
            user_id=request.state.user_id,
            username=request.state.username,
            path=request.url.path
        )

    except TokenError as e:
        logger.warning(
            "Token验证失败",
            error=str(e),
            path=request.url.path
        )

        # 返回401未授权错误
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": True,
                "code": "INVALID_TOKEN",
                "message": "无效的访问令牌",
            },
        )
    except Exception as e:
        logger.error(
            "认证中间件异常",
            error=str(e),
            path=request.url.path,
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "code": "AUTH_ERROR",
                "message": "认证服务异常",
            },
        )

    # 继续处理请求
    return await call_next(request)


async def require_auth_middleware(request: Request, call_next: Callable) -> Response:
    """
    强制认证中间件 - 所有请求都需要认证
    用于需要认证的路由组
    """
    # 获取Authorization头
    authorization = request.headers.get("Authorization")

    if not authorization:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": True,
                "code": "MISSING_TOKEN",
                "message": "缺少访问令牌",
            },
        )

    if not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": True,
                "code": "INVALID_TOKEN_FORMAT",
                "message": "无效的令牌格式",
            },
        )

    token = authorization.split(" ")[1]

    try:
        payload = verify_token(token)
        request.state.user_id = payload.get("sub")
        request.state.username = payload.get("username")

        if not request.state.user_id:
            raise TokenError("令牌中缺少用户信息")

    except TokenError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": True,
                "code": "INVALID_TOKEN",
                "message": "无效的访问令牌",
            },
        )

    return await call_next(request)


__all__ = [
    "auth_middleware",
    "require_auth_middleware",
]
