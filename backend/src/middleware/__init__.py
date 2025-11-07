"""
中间件模块 - 统一管理所有中间件
"""

# 导入所有中间件
from .auth import auth_middleware, require_auth_middleware
from .error import error_handler_middleware, not_found_handler, method_not_allowed_handler
from .logging import logging_middleware, request_details_middleware, performance_monitoring_middleware
from .security import security_middleware, https_redirect_middleware, rate_limit_middleware, cors_preflight_middleware

# 导出所有中间件
__all__ = [
    # 认证中间件
    "auth_middleware",
    "require_auth_middleware",

    # 错误处理中间件
    "error_handler_middleware",
    "not_found_handler",
    "method_not_allowed_handler",

    # 日志中间件
    "logging_middleware",
    "request_details_middleware",
    "performance_monitoring_middleware",

    # 安全中间件
    "security_middleware",
    "https_redirect_middleware",
    "rate_limit_middleware",
    "cors_preflight_middleware",
]