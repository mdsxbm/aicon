"""
AI导演引擎相关的Pydantic模式
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import UUIDMixin


class PromptGenerateRequest(BaseModel):
    """生成提示词请求模型"""
    chapter_id: UUID = Field(..., description="章节ID")
    api_key: str = Field(..., min_length=1, description="API密钥")
    provider: str = Field("volcengine", description="LLM供应商 (volcengine/deepseek)")
    model: Optional[str] = Field(None, description="模型名称")
    style: str = Field("cinematic", description="风格预设")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chapter_id": "123e4567-e89b-12d3-a456-426614174000",
                "api_key": "sk-xxxxx",
                "provider": "volcengine",
                "style": "cinematic"
            }
        }
    }


class PromptGenerateResponse(BaseModel):
    """生成提示词响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    updated_count: int = Field(0, description="更新的句子数量")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "成功为 100 个句子生成提示词",
                "updated_count": 100
            }
        }
    }


__all__ = [
    "PromptGenerateRequest",
    "PromptGenerateResponse",
]
