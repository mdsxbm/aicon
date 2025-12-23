"""
电影视频合成服务 - 专门处理电影分镜视频合成

负责:
- 获取章节的所有分镜视频
- 验证分镜视频完整性
- 并发下载分镜视频
- 拼接分镜视频
- 混合BGM
- 上传到MinIO

注意: 此服务不依赖Whisper模型,避免内存浪费
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.core.exceptions import BusinessLogicError
from src.core.logging import get_logger
from src.models import Chapter, VideoTask, VideoTaskStatus
from src.models.movie import MovieScript, MovieScene, MovieShot
from src.services.base import BaseService
from src.services.chapter import ChapterService
from src.services.video_task import VideoTaskService
from src.utils.ffmpeg_utils import (
    check_ffmpeg_installed,
    concatenate_videos,
    get_audio_duration,
    mix_bgm_with_video,
)
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class MovieVideoService(BaseService):
    """
    电影视频合成服务
    
    专门处理电影类型项目的视频合成,不依赖Whisper模型
    """

    def __init__(self, db_session):
        """初始化电影视频合成服务"""
        super().__init__(db_session)
        self.storage_client = None
        logger.debug("MovieVideoService 初始化完成")

    async def _get_storage_client(self):
        """获取存储客户端"""
        if self.storage_client is None:
            self.storage_client = await get_storage_client()
        return self.storage_client

    async def _get_chapter_shots(self, chapter_id: str) -> List[MovieShot]:
        """
        获取章节的所有分镜(按顺序)
        
        Args:
            chapter_id: 章节ID
            
        Returns:
            分镜列表(按场景和分镜顺序排序)
        """
        result = await self.db_session.execute(
            select(MovieShot)
            .join(MovieScene)
            .join(MovieScript)
            .where(MovieScript.chapter_id == chapter_id)
            .options(
                joinedload(MovieShot.scene)
                .joinedload(MovieScene.script)
            )
            .order_by(MovieScene.order_index, MovieShot.order_index)
        )
        
        shots = result.scalars().all()
        logger.info(f"章节 {chapter_id} 共有 {len(shots)} 个分镜")
        return shots

    async def _validate_shot_videos(self, shots: List[MovieShot]) -> None:
        """
        验证所有分镜都有视频
        
        Args:
            shots: 分镜列表
            
        Raises:
            BusinessLogicError: 如果有分镜缺少视频或状态不正确
        """
        missing_videos = []
        
        for shot in shots:
            if not shot.video_url:
                missing_videos.append(
                    f"场景{shot.scene.order_index}-分镜{shot.order_index}: 缺少视频"
                )
            elif shot.status != 'completed':
                missing_videos.append(
                    f"场景{shot.scene.order_index}-分镜{shot.order_index}: 状态={shot.status}"
                )
        
        if missing_videos:
            error_msg = f"分镜视频不完整,共{len(missing_videos)}个问题:\n" + "\n".join(missing_videos[:10])
            if len(missing_videos) > 10:
                error_msg += f"\n... 还有{len(missing_videos) - 10}个问题"
            raise BusinessLogicError(error_msg)
        
        logger.info(f"✅ 所有 {len(shots)} 个分镜视频验证通过")

    async def _download_shot_videos(
        self,
        shots: List[MovieShot],
        temp_dir: Path
    ) -> List[Path]:
        """
        并发下载所有分镜视频
        
        Args:
            shots: 分镜列表
            temp_dir: 临时目录
            
        Returns:
            下载后的本地视频路径列表(按顺序)
        """
        storage_client = await self._get_storage_client()
        
        async def download_one(shot: MovieShot, index: int) -> Path:
            """下载单个分镜视频"""
            video_path = temp_dir / f"shot_{index:03d}.mp4"
            
            try:
                logger.info(f"📥 下载分镜 {index + 1}/{len(shots)}: {shot.video_url}")
                content = await storage_client.download_file(shot.video_url)
                
                with open(video_path, 'wb') as f:
                    f.write(content)
                
                logger.info(f"✅ 分镜 {index + 1} 下载完成: {len(content)} bytes")
                return video_path
                
            except Exception as e:
                logger.error(f"❌ 分镜 {index + 1} 下载失败: {e}")
                raise BusinessLogicError(f"下载分镜视频失败: 场景{shot.scene.order_index}-分镜{shot.order_index}")
        
        # 并发下载,限制并发数为5
        semaphore = asyncio.Semaphore(5)
        
        async def download_with_limit(shot: MovieShot, idx: int) -> Path:
            async with semaphore:
                return await download_one(shot, idx)
        
        tasks = [
            download_with_limit(shot, idx)
            for idx, shot in enumerate(shots)
        ]
        
        logger.info(f"🚀 开始并发下载 {len(shots)} 个分镜视频(并发数:5)")
        video_paths = await asyncio.gather(*tasks)
        logger.info(f"✅ 所有分镜视频下载完成")
        
        return video_paths

    async def _concatenate_videos(
        self,
        video_paths: List[Path],
        temp_dir: Path
    ) -> Path:
        """
        拼接分镜视频
        
        Args:
            video_paths: 视频文件路径列表
            temp_dir: 临时目录
            
        Returns:
            拼接后的视频路径
        """
        final_video_path = temp_dir / "movie_final.mp4"
        concat_file_path = temp_dir / "concat.txt"
        
        logger.info(f"🎬 开始拼接 {len(video_paths)} 个分镜视频")
        
        success = concatenate_videos(
            video_paths,
            final_video_path,
            concat_file_path
        )
        
        if not success:
            raise BusinessLogicError("分镜视频拼接失败")
        
        logger.info(f"✅ 视频拼接完成: {final_video_path}")
        return final_video_path

    async def _mix_bgm(
        self,
        video_path: Path,
        task: VideoTask,
        temp_dir: Path
    ) -> Path:
        """
        混合BGM到视频
        
        Args:
            video_path: 视频文件路径
            task: 视频任务对象
            temp_dir: 临时目录
            
        Returns:
            混合BGM后的视频路径
        """
        try:
            logger.info(f"🎵 开始混合BGM: background_id={task.background_id}")
            
            # 1. 加载BGM信息
            from src.services.bgm_service import BGMService
            bgm_service = BGMService(self.db_session)
            bgm = await bgm_service.get_bgm_by_id(
                str(task.background_id),
                str(task.user_id)
            )
            
            if not bgm or not bgm.file_key:
                logger.warning("BGM不存在或无file_key,跳过BGM混合")
                return video_path
            
            # 2. 下载BGM文件
            storage = await self._get_storage_client()
            bgm_content = await storage.download_file(bgm.file_key)
            
            # 保存到临时文件
            import os
            bgm_ext = os.path.splitext(bgm.file_name)[1] or ".mp3"
            bgm_temp_path = temp_dir / f"bgm{bgm_ext}"
            with open(bgm_temp_path, 'wb') as f:
                f.write(bgm_content)
            
            logger.info(f"BGM下载成功: {bgm.name}, 大小={len(bgm_content)} bytes")
            
            # 3. 获取BGM音量配置
            gen_setting = task.get_gen_setting()
            bgm_volume = gen_setting.get("bgm_volume", 0.15)
            logger.info(f"BGM音量配置: {bgm_volume}")
            
            # 4. 混合BGM
            final_video_with_bgm_path = temp_dir / "movie_final_with_bgm.mp4"
            
            mix_success = mix_bgm_with_video(
                str(video_path),
                str(bgm_temp_path),
                str(final_video_with_bgm_path),
                bgm_volume=bgm_volume,
                loop_bgm=True
            )
            
            if mix_success:
                logger.info("✅ BGM混合成功")
                return final_video_with_bgm_path
            else:
                logger.warning("⚠️ BGM混合失败,使用原视频")
                return video_path
                
        except Exception as e:
            logger.error(f"BGM混合过程出错: {e}", exc_info=True)
            logger.warning("BGM混合失败,继续使用原视频")
            return video_path

    async def _upload_video(
        self,
        video_path: Path,
        task: VideoTask
    ) -> tuple[str, int]:
        """
        上传视频到MinIO
        
        Args:
            video_path: 本地视频文件路径
            task: 视频任务对象
            
        Returns:
            (video_key, duration) 元组
        """
        storage = await self._get_storage_client()
        
        # 生成对象键
        video_key = storage.generate_object_key(
            str(task.user_id),
            f"chapter_{task.chapter_id}_movie.mp4",
            prefix="videos"
        )
        
        logger.info(f"📤 开始上传视频到MinIO: {video_key}")
        
        # 读取文件并上传
        from fastapi import UploadFile
        with open(video_path, 'rb') as f:
            upload_file = UploadFile(
                filename=f"chapter_{task.chapter_id}_movie.mp4",
                file=f
            )
            result = await storage.upload_file(
                str(task.user_id),
                upload_file,
                object_key=video_key
            )
        
        video_key = result["object_key"]
        
        # 获取视频时长
        duration = int(get_audio_duration(str(video_path)) or 0)
        
        logger.info(f"✅ 视频上传完成: {video_key}, 时长: {duration}秒")
        return video_key, duration

    async def _update_chapter_video(
        self,
        chapter_id: str,
        video_key: str,
        duration: int
    ) -> None:
        """
        更新章节的视频URL和时长
        
        Args:
            chapter_id: 章节ID
            video_key: 视频对象键
            duration: 视频时长(秒)
        """
        chapter_service = ChapterService(self.db_session)
        chapter = await chapter_service.get_chapter_by_id(chapter_id)
        
        chapter.video_url = video_key
        chapter.video_duration = duration
        
        await self.db_session.flush()
        logger.info(f"✅ 章节视频信息已更新: video_url={video_key}, duration={duration}s")

    async def synthesize_movie_video(self, video_task_id: str) -> dict:
        """
        电影视频合成主流程
        
        Args:
            video_task_id: 视频任务ID
            
        Returns:
            统计信息字典
        """
        temp_dir = None
        
        try:
            # 检查FFmpeg
            if not check_ffmpeg_installed():
                raise BusinessLogicError("FFmpeg未安装或不可用")
            
            # 1. 加载视频任务
            task_service = VideoTaskService(self.db_session)
            task = await task_service.get_video_task_by_id(video_task_id)
            
            # 2. 验证任务状态
            if task.status not in [VideoTaskStatus.PENDING.value, VideoTaskStatus.FAILED.value]:
                raise BusinessLogicError(f"任务状态不正确: {task.status}")
            
            # 3. 更新状态为验证中
            await task_service.update_task_status(task.id, VideoTaskStatus.VALIDATING)
            
            # 4. 加载章节
            chapter_service = ChapterService(self.db_session)
            chapter = await chapter_service.get_chapter_by_id(task.chapter_id)
            
            # 5. 验证是电影类型
            if chapter.project.type != 'movie':
                raise BusinessLogicError(f"只支持电影类型项目,当前类型: {chapter.project.type}")
            
            logger.info(f"🎬 开始合成电影视频: chapter_id={task.chapter_id}")
            
            # 6. 获取所有分镜
            shots = await self._get_chapter_shots(task.chapter_id)
            
            if not shots:
                raise BusinessLogicError("章节没有分镜")
            
            # 7. 验证分镜视频完整性
            await self._validate_shot_videos(shots)
            
            # 8. 创建临时目录
            temp_dir = Path(tempfile.mkdtemp(prefix="movie_video_"))
            logger.info(f"创建临时目录: {temp_dir}")
            
            # 9. 更新状态为下载素材
            await task_service.update_task_status(task.id, VideoTaskStatus.DOWNLOADING_MATERIALS)
            task.update_progress(20)
            await self.db_session.flush()
            
            # 10. 并发下载所有分镜视频
            video_paths = await self._download_shot_videos(shots, temp_dir)
            
            # 11. 更新状态为拼接中
            await task_service.update_task_status(task.id, VideoTaskStatus.CONCATENATING)
            task.update_progress(60)
            await self.db_session.flush()
            
            # 12. 拼接视频
            final_video_path = await self._concatenate_videos(video_paths, temp_dir)
            
            # 13. 混合BGM(如果有)
            if task.background_id:
                task.update_progress(75)
                await self.db_session.flush()
                final_video_path = await self._mix_bgm(final_video_path, task, temp_dir)
            
            # 14. 更新状态为上传中
            await task_service.update_task_status(task.id, VideoTaskStatus.UPLOADING)
            task.update_progress(85)
            await self.db_session.flush()
            
            # 15. 上传到MinIO
            video_key, duration = await self._upload_video(final_video_path, task)
            
            # 16. 更新章节视频信息
            await self._update_chapter_video(task.chapter_id, video_key, duration)
            
            # 17. 标记任务完成
            await task_service.mark_task_completed(task.id, video_key, duration)
            task.update_progress(100)
            await self.db_session.flush()
            
            logger.info(f"🎉 电影视频合成完成: video_key={video_key}, duration={duration}s")
            
            return {
                "total_shots": len(shots),
                "video_key": video_key,
                "duration": duration
            }
            
        except Exception as e:
            logger.error(f"电影视频合成失败: {e}", exc_info=True)
            
            # 标记任务失败
            try:
                task_service = VideoTaskService(self.db_session)
                await task_service.mark_task_failed(video_task_id, str(e))
            except Exception as mark_error:
                logger.error(f"标记任务失败时出错: {mark_error}")
            
            raise
            
        finally:
            # 清理临时目录
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"清理临时目录: {temp_dir}")
                except Exception as e:
                    logger.error(f"清理临时目录失败: {e}")


__all__ = [
    "MovieVideoService",
]
