"""
安全中间件 - 处理安全相关功能
"""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.core.logging import logger


async def security_middleware(request: Request, call_next: Callable) -> Response:
    """安全中间件 - 基础安全检查"""
    # 检查请求方法
    if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        logger.warning(
            "不允许的HTTP方法",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        return JSONResponse(
            status_code=405,
            content={
                "error": True,
                "code": "METHOD_NOT_ALLOWED",
                "message": "不允许的HTTP方法",
            },
        )

    # 继续处理请求
    response = await call_next(request)

    # 添加基础安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


async def https_redirect_middleware(request: Request, call_next: Callable) -> Response:
    """HTTPS重定向中间件"""
    from src.core.config import settings

    # 生产环境强制HTTPS
    if (settings.ENVIRONMENT == "production" and
        request.headers.get("x-forwarded-proto") != "https"):

        logger.warning(
            "HTTP请求重定向到HTTPS",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # 返回301重定向
        return JSONResponse(
            status_code=301,
            headers={"Location": f"https://{request.url}{request.query_string}"},
            content={
                "error": True,
                "code": "HTTPS_REQUIRED",
                "message": "请使用HTTPS访问",
            },
        )

    return await call_next(request)


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """简单的限流中间件"""
    from src.core.config import settings
    import time
    from collections import defaultdict, deque

    # 如果未启用限流，直接通过
    if not getattr(settings, 'RATE_LIMIT_ENABLED', False):
        return await call_next(request)

    # 简单的内存限流实现（生产环境应使用Redis）
    if not hasattr(rate_limit_middleware, 'rate_limits'):
        rate_limit_middleware.rate_limits = defaultdict(deque)

    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    window_size = getattr(settings, 'RATE_LIMIT_WINDOW', 60)  # 默认60秒
    max_requests = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)  # 默认100次

    # 清理过期的请求记录
    rate_limits = rate_limit_middleware.rate_limits[client_ip]
    while rate_limits and rate_limits[0] < current_time - window_size:
        rate_limits.popleft()

    # 检查是否超过限流
    if len(rate_limits) >= max_requests:
        logger.warning(
            "请求频率超限",
            client_ip=client_ip,
            method=request.method,
            path=request.url.path,
            requests_count=len(rate_limits),
            window_size=window_size,
        )

        return JSONResponse(
            status_code=429,
            content={
                "error": True,
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "请求频率过高，请稍后再试",
                "retry_after": window_size,
            },
            headers={"Retry-After": str(window_size)},
        )

    # 记录当前请求
    rate_limits.append(current_time)

    return await call_next(request)


async def cors_preflight_middleware(request: Request, call_next: Callable) -> Response:
    """CORS预检请求处理中间件"""
    # 处理OPTIONS预检请求
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    return await call_next(request)


__all__ = [
    "security_middleware",
    "https_redirect_middleware",
    "rate_limit_middleware",
    "cors_preflight_middleware",
]