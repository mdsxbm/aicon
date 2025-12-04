"""
视频任务相关的Pydantic模式
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import PaginatedResponse, UUIDMixin


class VideoTaskCreate(BaseModel):
    """创建视频任务请求模型"""
    chapter_id: UUID = Field(..., description="章节ID")
    api_key_id: Optional[UUID] = Field(None, description="API密钥ID（可选，用于LLM字幕纠错）")
    gen_setting: Optional[Dict] = Field(None, description="生成设置")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chapter_id": "uuid-string",
                "api_key_id": "uuid-string",
                "gen_setting": {
                    "resolution": "1080x1920",
                    "fps": 30,
                    "video_codec": "libx264",
                    "audio_codec": "aac",
                    "audio_bitrate": "192k",
                    "zoom_speed": 0.0005,
                    "llm_model": "gpt-4o-mini",
                    "subtitle_style": {
                        "font": "Arial",
                        "font_size": 70,
                        "color": "white",
                        "position": "bottom"
                    }
                }
            }
        }
    }


class VideoTaskResponse(UUIDMixin):
    """视频任务响应模型"""
    id: UUID = Field(..., description="任务ID")
    user_id: UUID = Field(..., description="用户ID")
    project_id: UUID = Field(..., description="项目ID")
    chapter_id: UUID = Field(..., description="章节ID")
    api_key_id: Optional[UUID] = Field(None, description="API密钥ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(0, description="处理进度（0-100）")
    current_sentence_index: Optional[int] = Field(None, description="当前处理的句子索引")
    total_sentences: Optional[int] = Field(None, description="总句子数量")
    video_key: Optional[str] = Field(None, description="MinIO对象键")
    video_url: Optional[str] = Field(None, description="视频预签名URL")
    video_duration: Optional[int] = Field(None, description="视频时长（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    
    # 额外的关联信息
    chapter_title: Optional[str] = Field(None, description="章节标题")
    project_title: Optional[str] = Field(None, description="项目标题")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "VideoTaskResponse":
        """从字典创建响应对象，处理时间格式"""
        # 处理时间字段
        time_fields = ['created_at', 'updated_at']
        for field in time_fields:
            if field in data and data[field] is not None:
                if hasattr(data[field], 'isoformat'):
                    data[field] = data[field].isoformat()
                elif isinstance(data[field], str):
                    pass
                else:
                    data[field] = str(data[field])

        return cls(**data)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "uuid-string",
                "user_id": "user-uuid",
                "project_id": "project-uuid",
                "chapter_id": "chapter-uuid",
                "api_key_id": "api-key-uuid",
                "status": "synthesizing_videos",
                "progress": 45,
                "current_sentence_index": 10,
                "total_sentences": 25,
                "video_key": "videos/user_xxx/chapter_xxx_video.mp4",
                "video_url": "https://example.com/presigned-url",
                "video_duration": 180,
                "error_message": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:05:00Z",
                "chapter_title": "第一章：开始",
                "project_title": "我的项目"
            }
        }
    }


class VideoTaskListResponse(PaginatedResponse):
    """视频任务列表响应模型"""
    tasks: List[VideoTaskResponse] = Field(..., description="任务列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tasks": [
                    {
                        "id": "uuid-string",
                        "chapter_id": "chapter-uuid",
                        "status": "completed",
                        "progress": 100,
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "size": 20,
                "total_pages": 3
            }
        }
    }


class VideoTaskStatsResponse(BaseModel):
    """视频任务统计响应模型"""
    total: int = Field(0, description="总任务数")
    pending: int = Field(0, description="等待中")
    processing: int = Field(0, description="处理中")
    completed: int = Field(0, description="已完成")
    failed: int = Field(0, description="失败")
    success_rate: float = Field(0.0, description="成功率（0-100）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "pending": 5,
                "processing": 10,
                "completed": 80,
                "failed": 5,
                "success_rate": 94.1
            }
        }
    }


class VideoTaskDeleteResponse(BaseModel):
    """视频任务删除响应模型"""
    success: bool = Field(True, description="删除是否成功")
    message: str = Field("删除成功", description="响应消息")
    task_id: str = Field(..., description="删除的任务ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "删除成功",
                "task_id": "uuid-string"
            }
        }
    }


class VideoTaskRetryResponse(BaseModel):
    """视频任务重试响应模型"""
    success: bool = Field(True, description="重试是否成功")
    message: str = Field("任务已重新提交", description="响应消息")
    task: VideoTaskResponse = Field(..., description="重试后的任务信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "任务已重新提交",
                "task": {
                    "id": "uuid-string",
                    "status": "pending",
                    "progress": 0
                }
            }
        }
    }


__all__ = [
    "VideoTaskCreate",
    "VideoTaskResponse",
    "VideoTaskListResponse",
    "VideoTaskStatsResponse",
    "VideoTaskDeleteResponse",
    "VideoTaskRetryResponse",
]
