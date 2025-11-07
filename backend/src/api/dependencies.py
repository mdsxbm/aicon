"""
API依赖注入 - 简化版，只保留核心功能
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import TokenError, verify_token
from src.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    auto_error=False  # 不自动抛出错误，允许自定义处理
)


def get_current_user_optional(
        token: Optional[str] = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前认证用户（可选）"""
    if not token:
        return None

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            return None

        return user

    except TokenError:
        return None


def get_current_user_required(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户（必需）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except TokenError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )

    return user


# 常用依赖组合
def get_authenticated_user():
    """获取认证用户"""
    return Depends(get_current_user_required)


def get_optional_user():
    """获取可选认证用户"""
    return Depends(get_current_user_optional)


__all__ = [
    "get_current_user_optional",
    "get_current_user_required",
    "get_authenticated_user",
    "get_optional_user",
]
