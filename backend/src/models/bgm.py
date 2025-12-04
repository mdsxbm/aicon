"""
BGM (Background Music) 模型 - 背景音乐文件管理
"""

import uuid
from datetime import timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from src.core.logging import get_logger
from .base import BaseModel

logger = get_logger(__name__)


class BGMStatus(str, Enum):
    """BGM状态枚举"""
    UPLOADING = "uploading"  # 上传中
    ACTIVE = "active"  # 可用
    FAILED = "failed"  # 上传失败


class BGM(BaseModel):
    """BGM模型 - 背景音乐文件管理"""
    __tablename__ = 'bgm_files'

    # 基础字段 (ID, created_at, updated_at 继承自 BaseModel)
    user_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True, comment="用户ID")
    name = Column(String(200), nullable=False, comment="BGM名称")
    
    # 文件信息
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_key = Column(String(500), nullable=False, comment="MinIO对象键（存储路径）")
    file_url = Column(String(500), nullable=True, comment="文件预签名URL（按需生成）")
    
    # 音频信息
    duration = Column(Integer, nullable=True, comment="音频时长（秒）")
    
    # 状态
    status = Column(String(20), default=BGMStatus.ACTIVE, index=True, comment="BGM状态")

    # 关系定义
    user = relationship("User", foreign_keys=[user_id], lazy="noload")

    # 索引定义
    __table_args__ = (
        Index('idx_bgm_user', 'user_id'),
        Index('idx_bgm_status', 'status'),
        Index('idx_bgm_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<BGM(id={self.id}, name='{self.name}', duration={self.duration}s)>"

    def get_presigned_url(self, expires_hours: int = 24) -> Optional[str]:
        """
        生成文件预签名URL

        Args:
            expires_hours: 过期时间（小时）

        Returns:
            预签名URL，如果file_key不存在则返回None
        """
        if not self.file_key:
            return None

        try:
            from src.utils.storage import storage_client
            url = storage_client.get_presigned_url(
                self.file_key,
                timedelta(hours=expires_hours)
            )
            return url
        except Exception as e:
            logger.error(f"生成BGM预签名URL失败: {e}")
            return None

    def to_dict(self, exclude: Optional[list] = None) -> dict:
        """
        转换为字典，自动生成file_url
        
        Args:
            exclude: 要排除的字段列表
            
        Returns:
            字典表示
        """
        exclude = exclude or []
        result = super().to_dict(exclude=exclude)
        
        # 生成file_url（如果有file_key）
        if self.file_key and 'file_url' not in exclude:
            result['file_url'] = self.get_presigned_url()
        
        return result


__all__ = [
    "BGM",
    "BGMStatus",
]
