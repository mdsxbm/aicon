"""
视频任务模型 - 视频生成任务管理
严格按照data-model.md规范实现
"""

import json
import uuid
from datetime import timedelta
from enum import Enum
from typing import Dict, Optional

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from src.core.logging import get_logger
from .base import BaseModel

logger = get_logger(__name__)


class VideoTaskStatus(str, Enum):
    """视频任务状态枚举"""
    PENDING = "pending"  # 任务创建，等待开始
    VALIDATING = "validating"  # 验证章节素材
    DOWNLOADING_MATERIALS = "downloading_materials"  # 下载素材
    GENERATING_SUBTITLES = "generating_subtitles"  # 生成字幕时间轴
    SYNTHESIZING_VIDEOS = "synthesizing_videos"  # 合成单句视频
    CONCATENATING = "concatenating"  # 拼接视频
    UPLOADING = "uploading"  # 上传到MinIO
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败


class VideoTask(BaseModel):
    """视频任务模型 - 视频生成任务管理"""
    __tablename__ = 'video_tasks'

    # 基础字段 (ID, created_at, updated_at 继承自 BaseModel)
    user_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False, index=True, comment="用户ID（外键索引，无约束）")
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True, comment="项目ID（外键索引，无约束）")
    chapter_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey('chapters.id'), nullable=False, index=True, comment="章节ID（外键索引，无约束）")
    api_key_id = Column(PostgreSQLUUID(as_uuid=True), nullable=True, index=True, comment="API密钥ID（可选）")
    background_id = Column(PostgreSQLUUID(as_uuid=True), nullable=True, comment="背景音乐/图片ID（可选）")

    # 生成设置
    gen_setting = Column(Text, nullable=True, comment="生成设置（JSON格式）")

    # 处理状态
    status = Column(String(30), default=VideoTaskStatus.PENDING, index=True, comment="任务状态")
    progress = Column(Integer, default=0, comment="处理进度（0-100）")
    current_sentence_index = Column(Integer, nullable=True, comment="当前处理的句子索引（用于断点续传）")
    total_sentences = Column(Integer, nullable=True, comment="总句子数量")

    # 生成结果
    video_key = Column(String(500), nullable=True, comment="MinIO对象键（存储路径）")
    video_url = Column(String(500), nullable=True, comment="视频预签名URL（按需生成）")
    video_duration = Column(Integer, nullable=True, comment="视频时长（秒）")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_sentence_id = Column(PostgreSQLUUID(as_uuid=True), nullable=True, comment="出错的句子ID（用于调试）")

    # 关系定义
    from sqlalchemy.orm import relationship
    project = relationship("Project", foreign_keys=[project_id], lazy="noload")
    chapter = relationship("Chapter", foreign_keys=[chapter_id], lazy="noload")
    publish_tasks = relationship("PublishTask", back_populates="video_task", cascade="all, delete-orphan")

    # 索引定义
    __table_args__ = (
        Index('idx_video_task_user', 'user_id'),
        Index('idx_video_task_project', 'project_id'),
        Index('idx_video_task_chapter', 'chapter_id'),
        Index('idx_video_task_status', 'status'),
        Index('idx_video_task_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<VideoTask(id={self.id}, status={self.status}, progress={self.progress}%)>"

    def to_dict(self, exclude: Optional[list] = None) -> Dict:
        """
        转换为字典,自动解析gen_setting并生成video_url
        
        Args:
            exclude: 要排除的字段列表
            
        Returns:
            字典表示
        """
        exclude = exclude or []
        result = super().to_dict(exclude=exclude)
        
        # 解析gen_setting为JSON对象
        if 'gen_setting' in result and result['gen_setting']:
            try:
                result['gen_setting'] = json.loads(result['gen_setting'])
            except (json.JSONDecodeError, TypeError):
                result['gen_setting'] = {}
        else:
            result['gen_setting'] = {}
        
        # 生成video_url（如果有video_key）
        if self.video_key and 'video_url' not in exclude:
            result['video_url'] = self.get_video_url()
        
        return result

    def get_gen_setting(self) -> Dict:
        """
        获取生成设置（解析JSON）

        Returns:
            生成设置字典，如果未设置则返回默认值
        """
        if not self.gen_setting:
            return self._get_default_gen_setting()

        try:
            return json.loads(self.gen_setting)
        except json.JSONDecodeError as e:
            logger.error(f"解析生成设置失败: {e}, 使用默认设置")
            return self._get_default_gen_setting()

    def set_gen_setting(self, setting: Dict) -> None:
        """
        设置生成设置（转换为JSON）

        Args:
            setting: 生成设置字典
        """
        try:
            self.gen_setting = json.dumps(setting, ensure_ascii=False)
        except Exception as e:
            logger.error(f"设置生成设置失败: {e}")
            raise

    @staticmethod
    def _get_default_gen_setting() -> Dict:
        """获取默认生成设置（4:3横屏）"""
        return {
            "resolution": "1440x1080",  # 4:3横屏
            "fps": 30,
            "video_codec": "libx264",
            "audio_codec": "aac",
            "audio_bitrate": "192k",
            "zoom_speed": 0.0005,
            "subtitle_style": {
                "font": "Arial",
                "font_size": 70,  # 漫画解说标准字号
                "color": "white",
                "position": "bottom"
            }
        }

    def update_progress(self, progress: int, status: Optional[VideoTaskStatus] = None) -> None:
        """
        更新进度和状态

        Args:
            progress: 进度值（0-100）
            status: 可选的状态更新
        """
        self.progress = max(0, min(100, progress))
        if status:
            self.status = status.value if isinstance(status, VideoTaskStatus) else status
        logger.debug(f"视频任务 {self.id} 进度更新: {self.progress}%, 状态: {self.status}")

    def update_status(self, status: VideoTaskStatus, current_sentence: Optional[int] = None) -> None:
        """
        更新任务状态

        Args:
            status: 新状态
            current_sentence: 当前处理的句子索引
        """
        self.status = status.value if isinstance(status, VideoTaskStatus) else status
        if current_sentence is not None:
            self.current_sentence_index = current_sentence
        logger.info(f"视频任务 {self.id} 状态更新: {self.status}")

    def mark_as_completed(self, video_key: str, duration: int) -> None:
        """
        标记为完成

        Args:
            video_key: MinIO对象键
            duration: 视频时长（秒）
        """
        self.status = VideoTaskStatus.COMPLETED.value
        self.progress = 100
        self.video_key = video_key
        self.video_duration = duration
        self.error_message = None
        self.error_sentence_id = None
        logger.info(f"视频任务 {self.id} 完成: video_key={video_key}, duration={duration}s")

    def mark_as_failed(self, error: str, sentence_id: Optional[str] = None) -> None:
        """
        标记为失败

        Args:
            error: 错误信息
            sentence_id: 出错的句子ID
        """
        self.status = VideoTaskStatus.FAILED.value
        self.error_message = error
        if sentence_id:
            self.error_sentence_id = sentence_id
        logger.error(f"视频任务 {self.id} 失败: {error}")

    def get_video_url(self, expires_hours: int = 6) -> Optional[str]:
        """
        生成视频预签名URL

        Args:
            expires_hours: 过期时间（小时）

        Returns:
            预签名URL，如果video_key不存在则返回None
        """
        if not self.video_key:
            return None

        try:
            from src.utils.storage import storage_client
            url = storage_client.get_presigned_url(
                self.video_key,
                timedelta(hours=expires_hours)
            )
            return url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {e}")
            return None

    def can_resume(self) -> bool:
        """
        检查任务是否可以断点续传

        Returns:
            如果任务失败且有当前句子索引，则可以续传
        """
        return (
            self.status == VideoTaskStatus.FAILED.value and
            self.current_sentence_index is not None and
            self.current_sentence_index > 0
        )

    def reset_for_retry(self) -> None:
        """重置任务以便重试（保留current_sentence_index用于断点续传）"""
        self.status = VideoTaskStatus.PENDING.value
        self.progress = 0
        self.error_message = None
        self.error_sentence_id = None
        # 保留 current_sentence_index 用于断点续传
        logger.info(f"视频任务 {self.id} 重置为待处理状态，保留断点: {self.current_sentence_index}")


__all__ = [
    "VideoTask",
    "VideoTaskStatus",
]
