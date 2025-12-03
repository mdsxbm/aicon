"""
视频合成服务 - 视频生成的核心服务
"""

import asyncio
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.core.exceptions import BusinessLogicError, NotFoundError
from src.core.logging import get_logger
from src.models import Chapter, ChapterStatus, Sentence, VideoTask, VideoTaskStatus
from src.services.base import SessionManagedService
from src.services.chapter import ChapterService
from src.services.faster_whisper_service import transcription_service
from src.services.video_task import VideoTaskService
from src.utils.ffmpeg_utils import (
    build_sentence_video_command,
    check_ffmpeg_installed,
    concatenate_videos,
    get_audio_duration,
    run_ffmpeg_command,
)
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class VideoSynthesisService(SessionManagedService):
    """
    视频合成服务

    负责视频生成的完整流程，包括素材下载、字幕生成、视频合成和拼接。
    """

    def __init__(self):
        """初始化视频合成服务"""
        super().__init__()
        self.storage_client = None
        logger.debug("VideoSynthesisService 初始化完成")

    async def _get_storage_client(self):
        """获取存储客户端"""
        if self.storage_client is None:
            self.storage_client = await get_storage_client()
        return self.storage_client

    async def _validate_chapter_materials(self, chapter: Chapter) -> None:
        """
        验证章节素材是否准备好

        Args:
            chapter: 章节对象

        Raises:
            BusinessLogicError: 如果章节状态不正确或素材不完整
        """
        # 检查章节状态
        if chapter.status != ChapterStatus.MATERIALS_PREPARED.value:
            raise BusinessLogicError(
                f"章节状态不正确，当前状态: {chapter.status}，需要: {ChapterStatus.MATERIALS_PREPARED.value}"
            )

        # 获取章节的所有句子
        chapter_service = ChapterService(self.db_session)
        sentences = await chapter_service.get_sentences(chapter.id)

        if not sentences:
            raise BusinessLogicError("章节没有句子")

        # 检查每个句子是否有必要的素材
        missing_materials = []
        for sentence in sentences:
            if not sentence.image_url:
                missing_materials.append(f"句子 {sentence.id} 缺少图片")
            if not sentence.audio_url:
                missing_materials.append(f"句子 {sentence.id} 缺少音频")

        if missing_materials:
            raise BusinessLogicError(
                f"章节素材不完整:\n" + "\n".join(missing_materials[:5])  # 只显示前5个
            )

        logger.info(f"章节素材验证通过: {chapter.id}, 共 {len(sentences)} 个句子")

    async def _fetch_material_from_minio(self, object_key_or_url: str, dest_path: Path) -> None:
        """
        从MinIO下载素材（支持对象键或预签名URL）

        Args:
            object_key_or_url: MinIO对象键或预签名URL
            dest_path: 目标路径
        """
        try:
            # 判断是URL还是对象键
            if object_key_or_url.startswith('http://') or object_key_or_url.startswith('https://'):
                # 是预签名URL，提取对象键
                # URL格式: http://localhost:9000/bucket/path/to/file.jpg?X-Amz-...
                from urllib.parse import urlparse, unquote
                
                parsed = urlparse(object_key_or_url)
                # 路径格式: /bucket/path/to/file.jpg
                path_parts = parsed.path.split('/', 2)  # ['', 'bucket', 'path/to/file.jpg']
                
                if len(path_parts) >= 3:
                    object_key = unquote(path_parts[2])  # 'path/to/file.jpg'
                    logger.debug(f"从URL提取对象键: {object_key}")
                else:
                    raise ValueError(f"无法从URL提取对象键: {object_key_or_url}")
                
                # 使用对象键从MinIO下载
                storage = await self._get_storage_client()
                await storage.download_file_to_path(object_key, str(dest_path))
                logger.debug(f"下载素材成功: {object_key} -> {dest_path}")
            else:
                # 是对象键，直接从MinIO下载
                logger.debug(f"从MinIO下载素材: {object_key_or_url}")
                storage = await self._get_storage_client()
                await storage.download_file_to_path(object_key_or_url, str(dest_path))
                logger.debug(f"下载素材成功: {object_key_or_url} -> {dest_path}")
                
        except Exception as e:
            logger.error(f"下载素材失败: {object_key_or_url[:100] if len(object_key_or_url) > 100 else object_key_or_url}, 错误: {e}")
            raise

    def _generate_subtitle_timeline(self, audio_path: str) -> dict:
        """
        生成字幕时间轴

        Args:
            audio_path: 音频文件路径

        Returns:
            字幕数据，包含segments和duration
        """
        try:
            # 使用Whisper服务进行转录
            results, srt_content = transcription_service.transcribe(
                audio_path,
                output_format="json"
            )

            # 获取音频时长
            duration = get_audio_duration(audio_path) or 0

            return {
                "segments": results,
                "duration": duration
            }

        except Exception as e:
            logger.error(f"生成字幕时间轴失败: {e}")
            raise

    def _split_text_into_lines(self, text: str, max_chars: int = 18) -> list:
        """
        智能分割文本为双行字幕（漫画解说标准）
        
        Args:
            text: 要分割的文本
            max_chars: 每行最大字符数（推荐15-20字）
            
        Returns:
            分割后的行列表（最多2行，不含标点）
        """
        import re
        
        # 移除所有标点符号
        punctuation_pattern = r'[，。！？；、,\.!?;]'
        clean_text = re.sub(punctuation_pattern, '', text).strip()
        
        if not clean_text:
            return []
        
        # 如果文本很短，直接返回单行
        if len(clean_text) <= max_chars:
            return [clean_text]
        
        # 分成两行（漫画解说标准）
        # 尽量在中间位置分割
        mid_point = len(clean_text) // 2
        
        # 在中间点附近找最佳分割位置
        best_split = mid_point
        for i in range(max(mid_point - 5, 0), min(mid_point + 5, len(clean_text))):
            if i > 0 and i < len(clean_text):
                best_split = i
                break
        
        line1 = clean_text[:best_split].strip()
        line2 = clean_text[best_split:].strip()
        
        # 如果第二行太长，截断
        if len(line2) > max_chars:
            line2 = line2[:max_chars]
        
        # 如果第一行太长，调整
        if len(line1) > max_chars:
            line1 = line1[:max_chars]
        
        return [line1, line2] if line2 else [line1]

    def _create_subtitle_filter(
            self,
            subtitle_data: dict,
            gen_setting: dict
    ) -> str:
        """
        创建漫画解说字幕滤镜（固定位置，专业样式）

        Args:
            subtitle_data: 字幕数据
            gen_setting: 生成设置

        Returns:
            FFmpeg drawtext滤镜字符串
        """
        try:
            subtitle_style = gen_setting.get("subtitle_style", {})
            font_size = subtitle_style.get("font_size", 70)  # 适中字号
            color = subtitle_style.get("color", "white")

            # 固定位置：画面下方
            # 4:3横屏（1080px高度）：字幕固定在y=900
            fixed_y_pos = 900
            
            # 标点符号正则
            import re
            punctuation_pattern = r'[，。！？；、,\.!?;:\'"\(\)\[\]\{\}<>]'
            
            filters = []
            segments = subtitle_data.get("segments", [])

            for segment in segments:
                words = segment.get("words", [])
                
                if words:
                    # 使用词级时间轴构建字幕行
                    current_line_words = []
                    current_line_len = 0
                    
                    for w in words:
                        raw_word = w.get("word", "")
                        # 移除标点，但保留文字
                        clean_word = re.sub(punctuation_pattern, '', raw_word).strip()
                        
                        if not clean_word:
                            continue
                            
                        word_len = len(clean_word)
                        
                        # 如果加上这个词会超过最大长度（18字），则先输出当前行
                        if current_line_len + word_len > 18 and current_line_words:
                            # 生成当前行的滤镜
                            line_text = "".join([x["text"] for x in current_line_words])
                            start_time = current_line_words[0]["start"]
                            end_time = current_line_words[-1]["end"]
                            
                            # 转义特殊字符
                            text_escaped = line_text.replace("'", "'\\\\\\''").replace(":", "\\:")
                            
                            filter_str = (
                                f"drawtext="
                                f"text='{text_escaped}':"
                                f"fontsize={font_size}:"
                                f"fontcolor={color}:"
                                f"borderw=5:"
                                f"bordercolor=black:"
                                f"shadowcolor=black@0.7:"
                                f"shadowx=4:"
                                f"shadowy=4:"
                                f"box=1:"
                                f"boxcolor=black@0.65:"
                                f"boxborderw=20:"
                                f"x=(w-text_w)/2:"
                                f"y={fixed_y_pos}:"
                                f"enable='between(t,{start_time:.3f},{end_time:.3f})'"
                            )
                            filters.append(filter_str)
                            
                            # 重置行
                            current_line_words = []
                            current_line_len = 0
                        
                        # 添加词到当前行
                        current_line_words.append({
                            "text": clean_word,
                            "start": w.get("start", 0),
                            "end": w.get("end", 0)
                        })
                        current_line_len += word_len
                    
                    # 处理最后一行
                    if current_line_words:
                        line_text = "".join([x["text"] for x in current_line_words])
                        start_time = current_line_words[0]["start"]
                        end_time = current_line_words[-1]["end"]
                        
                        text_escaped = line_text.replace("'", "'\\\\\\''").replace(":", "\\:")
                        
                        filter_str = (
                            f"drawtext="
                            f"text='{text_escaped}':"
                            f"fontsize={font_size}:"
                            f"fontcolor={color}:"
                            f"borderw=5:"
                            f"bordercolor=black:"
                            f"shadowcolor=black@0.7:"
                            f"shadowx=4:"
                            f"shadowy=4:"
                            f"box=1:"
                            f"boxcolor=black@0.65:"
                            f"boxborderw=20:"
                            f"x=(w-text_w)/2:"
                            f"y={fixed_y_pos}:"
                            f"enable='between(t,{start_time:.3f},{end_time:.3f})'"
                        )
                        filters.append(filter_str)
                        
                else:
                    # 没有词级时间轴，使用比例计算时间（回退方案）
                    text = segment.get("text", "").strip()
                    # 移除标点
                    clean_text = re.sub(punctuation_pattern, '', text).strip()
                    
                    if not clean_text:
                        continue
                    
                    # 智能分割
                    lines = self._split_text_into_lines(clean_text, max_chars=18)
                    
                    segment_start = segment.get("start", 0)
                    segment_end = segment.get("end", 0)
                    total_duration = segment_end - segment_start
                    total_length = len(clean_text.replace(" ", ""))
                    
                    current_start = segment_start
                    
                    for line_text in lines:
                        if not line_text.strip():
                            continue
                        
                        # 按长度比例计算持续时间
                        line_len = len(line_text)
                        if total_length > 0:
                            line_duration = total_duration * (line_len / total_length)
                        else:
                            line_duration = total_duration / len(lines)
                            
                        line_end = current_start + line_duration
                        
                        text_escaped = line_text.replace("'", "'\\\\\\''").replace(":", "\\:")
                        
                        filter_str = (
                            f"drawtext="
                            f"text='{text_escaped}':"
                            f"fontsize={font_size}:"
                            f"fontcolor={color}:"
                            f"borderw=5:"
                            f"bordercolor=black:"
                            f"shadowcolor=black@0.7:"
                            f"shadowx=4:"
                            f"shadowy=4:"
                            f"box=1:"
                            f"boxcolor=black@0.65:"
                            f"boxborderw=20:"
                            f"x=(w-text_w)/2:"
                            f"y={fixed_y_pos}:"
                            f"enable='between(t,{current_start:.3f},{line_end:.3f})'"
                        )
                        filters.append(filter_str)
                        
                        current_start = line_end

            if not filters:
                return ""

            return ",".join(filters)

        except Exception as e:
            logger.error(f"创建字幕滤镜失败: {e}", exc_info=True)
            return ""

    async def _synthesize_sentence_video(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict
    ) -> Path:
        """
        合成单个句子的视频

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置

        Returns:
            生成的视频文件路径
        """
        try:
            # 创建句子专用目录
            sentence_dir = temp_dir / f"sentence_{index:03d}"
            sentence_dir.mkdir(parents=True, exist_ok=True)

            # 下载图片
            image_path = sentence_dir / f"image.jpg"
            await self._fetch_material_from_minio(sentence.image_url, image_path)

            # 下载音频
            audio_path = sentence_dir / f"audio.mp3"
            await self._fetch_material_from_minio(sentence.audio_url, audio_path)

            # 生成字幕时间轴
            subtitle_data = self._generate_subtitle_timeline(str(audio_path))

            # 创建字幕滤镜
            subtitle_filter = self._create_subtitle_filter(subtitle_data, gen_setting)

            # 输出视频路径
            output_path = sentence_dir / f"video.mp4"

            # 构建FFmpeg命令
            command = build_sentence_video_command(
                str(image_path),
                str(audio_path),
                str(output_path),
                subtitle_filter,
                gen_setting
            )

            # 执行FFmpeg命令
            success, stdout, stderr = run_ffmpeg_command(command, timeout=300)

            if not success:
                raise Exception(f"FFmpeg执行失败: {stderr}")

            logger.info(f"句子视频合成成功: 索引={index}, 输出={output_path}")
            return output_path

        except Exception as e:
            logger.error(f"句子视频合成失败: 索引={index}, 错误={e}")
            raise

    async def _process_sentence_async(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict,
            semaphore: asyncio.Semaphore
    ) -> Tuple[bool, Optional[Path], Optional[Exception]]:
        """
        异步处理单个句子（带并发控制）

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置
            semaphore: 并发控制信号量

        Returns:
            (是否成功, 视频路径, 异常对象)
        """
        async with semaphore:
            try:
                video_path = await self._synthesize_sentence_video(
                    sentence, temp_dir, index, gen_setting
                )
                return True, video_path, None
            except Exception as e:
                logger.error(f"处理句子失败: {sentence.id}, 错误: {e}")
                return False, None, e

    async def synthesize_video(self, video_task_id: str) -> dict:
        """
        合成视频（主流程）

        Args:
            video_task_id: 视频任务ID

        Returns:
            统计信息字典
        """
        async with self:
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
                    raise BusinessLogicError(
                        f"任务状态不正确: {task.status}"
                    )

                # 3. 更新状态为验证中
                await task_service.update_task_status(task.id, VideoTaskStatus.VALIDATING)

                # 4. 加载章节并验证素材
                chapter_service = ChapterService(self.db_session)
                chapter = await chapter_service.get_chapter_by_id(task.chapter_id)
                await self._validate_chapter_materials(chapter)

                # 5. 解析生成设置
                gen_setting = task.get_gen_setting()

                # 6. 更新状态为下载素材
                await task_service.update_task_status(task.id, VideoTaskStatus.DOWNLOADING_MATERIALS)

                # 7. 获取所有句子
                sentences = await chapter_service.get_sentences(task.chapter_id)
                task.total_sentences = len(sentences)
                await self.db_session.flush()

                # 8. 创建临时目录
                temp_dir = Path(tempfile.mkdtemp(prefix="video_synthesis_"))
                logger.info(f"创建临时目录: {temp_dir}")

                # 9. 更新状态为合成视频
                await task_service.update_task_status(
                    task.id,
                    VideoTaskStatus.SYNTHESIZING_VIDEOS
                )

                # 10. 并发处理所有句子
                semaphore = asyncio.Semaphore(3)  # 限制并发数为3
                tasks_list = [
                    self._process_sentence_async(
                        sentence, temp_dir, idx, gen_setting, semaphore
                    )
                    for idx, sentence in enumerate(sentences)
                ]

                results = await asyncio.gather(*tasks_list, return_exceptions=True)

                # 11. 统计结果
                success_count = 0
                failed_count = 0
                video_paths = []

                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"句子 {idx} 处理异常: {result}")
                    else:
                        success, video_path, error = result
                        if success and video_path:
                            success_count += 1
                            video_paths.append(video_path)
                            # 更新进度
                            progress = int((idx + 1) / len(sentences) * 80)  # 0-80%
                            task.update_progress(progress)
                            task.current_sentence_index = idx
                            await self.db_session.flush()
                        else:
                            failed_count += 1

                if failed_count > 0:
                    raise BusinessLogicError(
                        f"部分句子处理失败: 成功={success_count}, 失败={failed_count}"
                    )

                # 12. 更新状态为拼接中
                await task_service.update_task_status(task.id, VideoTaskStatus.CONCATENATING)
                task.update_progress(85)
                await self.db_session.flush()

                # 13. 拼接视频
                final_video_path = temp_dir / "final_video.mp4"
                concat_file_path = temp_dir / "concat.txt"

                success = concatenate_videos(video_paths, final_video_path, concat_file_path)
                if not success:
                    raise BusinessLogicError("视频拼接失败")

                # 14. 更新状态为上传中
                await task_service.update_task_status(task.id, VideoTaskStatus.UPLOADING)
                task.update_progress(90)
                await self.db_session.flush()

                # 15. 上传到MinIO
                storage = await self._get_storage_client()
                video_key = storage.generate_object_key(
                    str(task.user_id),
                    f"chapter_{task.chapter_id}_video.mp4",
                    prefix="videos"
                )

                # 读取文件并上传
                from fastapi import UploadFile
                with open(final_video_path, 'rb') as f:
                    upload_file = UploadFile(
                        filename=f"chapter_{task.chapter_id}_video.mp4",
                        file=f
                    )
                    result = await storage.upload_file(
                        str(task.user_id),
                        upload_file,
                        object_key=video_key
                    )

                video_key = result["object_key"]

                # 16. 获取视频时长
                duration = int(get_audio_duration(str(final_video_path)) or 0)

                # 17. 标记任务完成
                await task_service.mark_task_completed(task.id, video_key, duration)
                task.update_progress(100)
                await self.db_session.flush()

                logger.info(f"视频合成完成: task_id={task.id}, video_key={video_key}")

                return {
                    "total": len(sentences),
                    "success": success_count,
                    "failed": failed_count,
                    "video_key": video_key,
                    "duration": duration
                }

            except Exception as e:
                logger.error(f"视频合成失败: {e}", exc_info=True)

                # 标记任务失败
                try:
                    task_service = VideoTaskService(self.db_session)
                    await task_service.mark_task_failed(
                        video_task_id,
                        str(e)
                    )
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


# 创建全局实例
video_synthesis_service = VideoSynthesisService()

__all__ = [
    "VideoSynthesisService",
    "video_synthesis_service",
]
