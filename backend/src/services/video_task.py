"""
视频任务服务 - 视频任务的CRUD操作
"""

from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessLogicError, NotFoundError
from src.core.logging import get_logger
from src.models.video_task import VideoTask, VideoTaskStatus
from src.services.base import BaseService

logger = get_logger(__name__)


class VideoTaskService(BaseService):
    """
    视频任务管理服务

    负责视频任务的完整生命周期管理，包括创建、查询、更新和状态管理。
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        初始化视频任务服务

        Args:
            db_session: 可选的数据库会话
        """
        super().__init__(db_session)
        logger.debug(f"VideoTaskService 初始化完成，会话管理: {'外部注入' if db_session else '自管理'}")

    async def create_video_task(
            self,
            user_id: str,
            project_id: str,
            chapter_id: str,
            api_key_id: Optional[str] = None,
            background_id: Optional[str] = None,
            gen_setting: Optional[dict] = None
    ) -> VideoTask:
        """
        创建新的视频任务

        Args:
            user_id: 用户ID
            project_id: 项目ID
            chapter_id: 章节ID
            api_key_id: API密钥ID（可选）
            background_id: 背景音乐/图片ID（可选）
            gen_setting: 生成设置（可选）

        Returns:
            创建的视频任务对象
        """
        try:
            # 创建视频任务对象
            video_task = VideoTask(
                user_id=user_id,
                project_id=project_id,
                chapter_id=chapter_id,
                api_key_id=api_key_id,
                background_id=background_id,
                status=VideoTaskStatus.PENDING
            )

            # 设置生成设置
            if gen_setting:
                video_task.set_gen_setting(gen_setting)

            await self.add(video_task)
            await self.commit()
            await self.refresh(video_task)

            logger.info(f"创建视频任务成功: ID={video_task.id}, 章节={chapter_id}")
            return video_task

        except Exception:
            await self.rollback()
            raise

    async def get_video_task_by_id(
            self,
            task_id: str,
            user_id: Optional[str] = None
    ) -> VideoTask:
        """
        根据ID获取视频任务

        Args:
            task_id: 任务ID
            user_id: 用户ID（可选，用于权限验证）

        Returns:
            视频任务对象

        Raises:
            NotFoundError: 当任务不存在或无权限访问时
        """
        query = select(VideoTask).filter(VideoTask.id == task_id)
        if user_id:
            query = query.filter(VideoTask.user_id == user_id)

        result = await self.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            error_message = "视频任务不存在或无权限访问" if user_id else "视频任务不存在"
            raise NotFoundError(
                error_message,
                resource_type="video_task",
                resource_id=task_id
            )

        logger.debug(f"获取视频任务成功: ID={task_id}, 状态={task.status}")
        return task

    async def get_user_video_tasks(
            self,
            user_id: str,
            status: Optional[VideoTaskStatus] = None,
            page: int = 1,
            size: int = 20
    ) -> Tuple[List[VideoTask], int]:
        """
        获取用户的视频任务列表（分页）

        Args:
            user_id: 用户ID
            status: 任务状态过滤（可选）
            page: 页码，从1开始
            size: 每页大小

        Returns:
            (任务列表, 总记录数)
        """
        # 参数验证
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = min(max(size, 1), 100)

        # 构建基础查询
        query = select(VideoTask).filter(VideoTask.user_id == user_id)

        # 状态过滤
        if status:
            query = query.filter(VideoTask.status == status.value)

        # 获取总数
        count_query = select(func.count(VideoTask.id)).filter(VideoTask.user_id == user_id)
        if status:
            count_query = count_query.filter(VideoTask.status == status.value)

        total_result = await self.execute(count_query)
        total = total_result.scalar()

        # 排序和分页
        query = query.order_by(desc(VideoTask.created_at))
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 执行查询
        result = await self.execute(query)
        tasks = result.scalars().all()

        logger.debug(f"查询用户视频任务: 用户={user_id}, 总数={total}, 当前页={page}")
        return list(tasks), total

    async def update_task_status(
            self,
            task_id: str,
            status: VideoTaskStatus,
            current_sentence: Optional[int] = None
    ) -> VideoTask:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            current_sentence: 当前处理的句子索引（可选）

        Returns:
            更新后的任务
        """
        task = await self.get_video_task_by_id(task_id)
        task.update_status(status, current_sentence)

        await self.commit()
        await self.refresh(task)

        logger.info(f"更新任务状态: ID={task_id}, 状态={status.value}")
        return task

    async def update_task_progress(
            self,
            task_id: str,
            progress: int
    ) -> VideoTask:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度值（0-100）

        Returns:
            更新后的任务
        """
        task = await self.get_video_task_by_id(task_id)
        task.update_progress(progress)

        await self.commit()
        await self.refresh(task)

        logger.debug(f"更新任务进度: ID={task_id}, 进度={progress}%")
        return task

    async def mark_task_completed(
            self,
            task_id: str,
            video_key: str,
            duration: int
    ) -> VideoTask:
        """
        标记任务为完成

        Args:
            task_id: 任务ID
            video_key: MinIO对象键
            duration: 视频时长（秒）

        Returns:
            更新后的任务
        """
        task = await self.get_video_task_by_id(task_id)
        task.mark_as_completed(video_key, duration)

        await self.commit()
        await self.refresh(task)

        logger.info(f"任务完成: ID={task_id}, video_key={video_key}, duration={duration}s")
        return task

    async def mark_task_failed(
            self,
            task_id: str,
            error_message: str,
            sentence_id: Optional[str] = None
    ) -> VideoTask:
        """
        标记任务为失败

        Args:
            task_id: 任务ID
            error_message: 错误信息
            sentence_id: 出错的句子ID（可选）

        Returns:
            更新后的任务
        """
        task = await self.get_video_task_by_id(task_id)
        task.mark_as_failed(error_message, sentence_id)

        await self.commit()
        await self.refresh(task)

        logger.error(f"任务失败: ID={task_id}, 错误={error_message}")
        return task

    async def retry_task(self, task_id: str) -> VideoTask:
        """
        重试失败的任务

        Args:
            task_id: 任务ID

        Returns:
            重置后的任务

        Raises:
            BusinessLogicError: 如果任务状态不是FAILED
        """
        task = await self.get_video_task_by_id(task_id)

        if task.status != VideoTaskStatus.FAILED.value:
            raise BusinessLogicError(
                f"只能重试失败的任务，当前状态: {task.status}"
            )

        task.reset_for_retry()

        await self.commit()
        await self.refresh(task)

        logger.info(f"任务重试: ID={task_id}, 断点索引={task.current_sentence_index}")
        return task

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """
        删除视频任务

        Args:
            task_id: 任务ID
            user_id: 用户ID（用于权限验证）

        Returns:
            是否删除成功
        """
        task = await self.get_video_task_by_id(task_id, user_id)

        # 如果任务正在处理中，不允许删除
        if task.status in [
            VideoTaskStatus.VALIDATING.value,
            VideoTaskStatus.DOWNLOADING_MATERIALS.value,
            VideoTaskStatus.GENERATING_SUBTITLES.value,
            VideoTaskStatus.SYNTHESIZING_VIDEOS.value,
            VideoTaskStatus.CONCATENATING.value,
            VideoTaskStatus.UPLOADING.value
        ]:
            raise BusinessLogicError(
                "正在处理中的任务不能删除"
            )

        await self.delete(task)
        await self.commit()

        logger.info(f"删除视频任务: ID={task_id}")
        return True

    async def list_user_tasks(
            self,
            user_id: str,
            page: int = 1,
            size: int = 20,
            status: Optional[VideoTaskStatus] = None,
            chapter_id: Optional[str] = None,
            project_id: Optional[str] = None,
            sort_by: str = "created_at",
            sort_order: str = "desc"
    ) -> Tuple[List[VideoTask], int]:
        """
        获取用户的视频任务列表（分页，带过滤和排序）

        Args:
            user_id: 用户ID
            page: 页码，从1开始
            size: 每页大小
            status: 任务状态过滤（可选）
            chapter_id: 章节ID过滤（可选）
            project_id: 项目ID过滤（可选）
            sort_by: 排序字段
            sort_order: 排序顺序（asc/desc）

        Returns:
            (任务列表, 总记录数)
        """
        # 参数验证
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = min(max(size, 1), 100)

        # 构建基础查询
        query = select(VideoTask).filter(VideoTask.user_id == user_id)

        # 状态过滤
        if status:
            query = query.filter(VideoTask.status == status.value)

        # 章节过滤
        if chapter_id:
            query = query.filter(VideoTask.chapter_id == chapter_id)

        # 项目过滤
        if project_id:
            query = query.filter(VideoTask.project_id == project_id)

        # 获取总数
        count_query = select(func.count(VideoTask.id)).filter(VideoTask.user_id == user_id)
        if status:
            count_query = count_query.filter(VideoTask.status == status.value)
        if chapter_id:
            count_query = count_query.filter(VideoTask.chapter_id == chapter_id)
        if project_id:
            count_query = count_query.filter(VideoTask.project_id == project_id)

        total_result = await self.execute(count_query)
        total = total_result.scalar()

        # 排序
        sort_column = getattr(VideoTask, sort_by, VideoTask.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 预加载关联的章节和项目信息
        from sqlalchemy.orm import selectinload
        query = query.options(
            selectinload(VideoTask.chapter),
            selectinload(VideoTask.project)
        )

        # 执行查询
        result = await self.execute(query)
        tasks = result.scalars().all()

        logger.debug(f"查询用户视频任务: 用户={user_id}, 总数={total}, 当前页={page}")
        return list(tasks), total

    async def get_task_stats(self, user_id: str) -> dict:
        """
        获取用户的视频任务统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        # 总任务数
        total_query = select(func.count(VideoTask.id)).filter(VideoTask.user_id == user_id)
        total_result = await self.execute(total_query)
        total = total_result.scalar()

        # 各状态任务数
        pending_query = select(func.count(VideoTask.id)).filter(
            VideoTask.user_id == user_id,
            VideoTask.status == VideoTaskStatus.PENDING.value
        )
        pending_result = await self.execute(pending_query)
        pending = pending_result.scalar()

        # 处理中的任务（包括多个中间状态）
        processing_query = select(func.count(VideoTask.id)).filter(
            VideoTask.user_id == user_id,
            VideoTask.status.in_([
                VideoTaskStatus.VALIDATING.value,
                VideoTaskStatus.DOWNLOADING_MATERIALS.value,
                VideoTaskStatus.GENERATING_SUBTITLES.value,
                VideoTaskStatus.SYNTHESIZING_VIDEOS.value,
                VideoTaskStatus.CONCATENATING.value,
                VideoTaskStatus.UPLOADING.value
            ])
        )
        processing_result = await self.execute(processing_query)
        processing = processing_result.scalar()

        # 已完成
        completed_query = select(func.count(VideoTask.id)).filter(
            VideoTask.user_id == user_id,
            VideoTask.status == VideoTaskStatus.COMPLETED.value
        )
        completed_result = await self.execute(completed_query)
        completed = completed_result.scalar()

        # 失败
        failed_query = select(func.count(VideoTask.id)).filter(
            VideoTask.user_id == user_id,
            VideoTask.status == VideoTaskStatus.FAILED.value
        )
        failed_result = await self.execute(failed_query)
        failed = failed_result.scalar()

        # 计算成功率
        success_rate = 0.0
        if completed + failed > 0:
            success_rate = round((completed / (completed + failed)) * 100, 1)

        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "success_rate": success_rate
        }

    async def delete_video_task(self, task_id: str) -> bool:
        """
        删除视频任务（不验证用户，由API层验证）

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        task = await self.get_video_task_by_id(task_id)

        # 如果任务正在处理中，不允许删除
        if task.status in [
            VideoTaskStatus.VALIDATING.value,
            VideoTaskStatus.DOWNLOADING_MATERIALS.value,
            VideoTaskStatus.GENERATING_SUBTITLES.value,
            VideoTaskStatus.SYNTHESIZING_VIDEOS.value,
            VideoTaskStatus.CONCATENATING.value,
            VideoTaskStatus.UPLOADING.value
        ]:
            raise BusinessLogicError(
                "正在处理中的任务不能删除"
            )

        await self.delete(task)
        await self.commit()

        logger.info(f"删除视频任务: ID={task_id}")
        return True


__all__ = [
    "VideoTaskService",
]
