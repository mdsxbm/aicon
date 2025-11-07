"""
认证相关的Pydantic模式 - 简化版
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """用户注册模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """验证用户名"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePassword123!",
                "display_name": "John Doe"
            }
        }
    }


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "password": "SecurePassword123!"
            }
        }
    }


class UserResponse(BaseModel):
    """用户响应模式"""
    id: str
    username: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: str
    last_login: Optional[str]
    timezone: str
    language: str

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def from_orm(cls, user):
        """从ORM模型创建响应对象"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None,
            timezone=user.timezone,
            language=user.language,
        )


class TokenResponse(BaseModel):
    """令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: Optional[UserResponse] = Field(None, description="用户信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "uuid-string",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "is_verified": True,
                    "is_active": True
                }
            }
        }
    }


class MessageResponse(BaseModel):
    """消息响应模式"""
    message: str = Field(..., description="响应消息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "操作成功"
            }
        }
    }


__all__ = [
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
]