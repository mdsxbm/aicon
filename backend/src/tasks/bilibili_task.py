"""
Bilibili发布Celery任务
"""

from typing import Dict, Any

from src.core.logging import get_logger
from src.tasks.app import celery_app
from src.tasks.base import async_task_decorator
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=0,
    name="bilibili.upload_chapter"
)
@async_task_decorator
async def upload_chapter_to_bilibili(
    db_session: AsyncSession,
    self,
    publish_task_id: str,
    user_id: str
) -> Dict[str, Any]:
    """上传章节视频到B站的 Celery 任务"""
    logger.info(f"Celery任务开始: upload_chapter_to_bilibili (publish_task_id={publish_task_id})")
    
    from src.services.bilibili import BilibiliPublishService
    
    service = BilibiliPublishService(db_session)
    result = await service.upload_chapter_task(
        publish_task_id=publish_task_id,
        user_id=user_id,
        celery_task_id=self.request.id
    )
    
    logger.info(f"Celery任务完成: upload_chapter_to_bilibili (publish_task_id={publish_task_id})")
    return result


__all__ = [
    "upload_chapter_to_bilibili",
]
