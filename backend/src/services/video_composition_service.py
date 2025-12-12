"""
视频合成服务 - 处理FFmpeg视频操作

负责:
- 合成单个句子的视频
- 执行FFmpeg命令
- 视频拼接
"""

from pathlib import Path
from typing import Optional

from src.core.logging import get_logger
from src.models import Sentence, APIKey
from src.services.material_service import material_service
from src.services.subtitle_service import subtitle_service
from src.utils.ffmpeg_utils import (
    build_sentence_video_command,
    run_ffmpeg_command,
)

logger = get_logger(__name__)


class VideoCompositionService:
    """视频合成服务 - 处理FFmpeg视频操作"""

    async def synthesize_sentence_video(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict,
            api_key: Optional[APIKey] = None,
            model: Optional[str] = None
    ) -> Path:
        """
        合成单个句子的视频

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置
            api_key: API密钥（可选，用于LLM纠错）
            model: 模型名称（可选）

        Returns:
            生成的视频文件路径
        """
        try:
            # 创建句子专用目录
            sentence_dir = temp_dir / f"sentence_{index:03d}"
            sentence_dir.mkdir(parents=True, exist_ok=True)

            # 下载图片
            image_path = sentence_dir / f"image.jpg"
            await material_service.fetch_material_from_minio(sentence.image_url, image_path)

            # 下载音频
            audio_path = sentence_dir / f"audio.mp3"
            await material_service.fetch_material_from_minio(sentence.audio_url, audio_path)

            # 生成字幕时间轴
            subtitle_data = subtitle_service.generate_subtitle_timeline(str(audio_path),sentence.content)

            # 如果提供了API密钥，使用LLM纠正字幕
            if api_key:
                logger.info(f"[LLM纠错] 句子 {index} 使用LLM纠正字幕")
                subtitle_data = await subtitle_service.correct_subtitle_with_llm(
                    subtitle_data=subtitle_data,
                    original_text=sentence.content,
                    api_key=api_key,
                    model=model
                )

            # 创建字幕滤镜
            subtitle_filter = subtitle_service.create_subtitle_filter(subtitle_data, gen_setting)

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


# 创建全局实例
video_composition_service = VideoCompositionService()

__all__ = [
    "VideoCompositionService",
    "video_composition_service",
]
