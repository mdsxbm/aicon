"""
FFmpeg工具函数 - 视频处理相关的FFmpeg操作
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)


def check_ffmpeg_installed() -> bool:
    """
    检查FFmpeg是否已安装

    Returns:
        如果FFmpeg可用返回True，否则返回False
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("FFmpeg已安装并可用")
            return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.error(f"FFmpeg检查失败: {e}")
        return False


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    获取音频文件时长

    Args:
        audio_path: 音频文件路径

    Returns:
        音频时长（秒），如果失败返回None
    """
    try:
        # 使用ffprobe获取音频时长
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            duration = float(result.stdout.strip())
            logger.debug(f"音频时长: {audio_path} = {duration}秒")
            return duration
        else:
            logger.error(f"获取音频时长失败: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"获取音频时长异常: {e}")
        return None


def create_concat_file(video_paths: List[Path], output_path: Path) -> None:
    """
    创建FFmpeg concat文件

    Args:
        video_paths: 视频文件路径列表
        output_path: concat文件输出路径
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                # 使用绝对路径并转义特殊字符
                abs_path = video_path.absolute()
                # FFmpeg concat文件格式: file 'path'
                f.write(f"file '{abs_path}'\n")

        logger.info(f"创建concat文件成功: {output_path}, 包含{len(video_paths)}个视频")

    except Exception as e:
        logger.error(f"创建concat文件失败: {e}")
        raise


def run_ffmpeg_command(command: List[str], timeout: int = 300) -> Tuple[bool, str, str]:
    """
    执行FFmpeg命令

    Args:
        command: FFmpeg命令列表
        timeout: 超时时间（秒），默认300秒

    Returns:
        (是否成功, 标准输出, 标准错误)
    """
    try:
        logger.info(f"执行FFmpeg命令: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        success = result.returncode == 0

        if success:
            logger.info("FFmpeg命令执行成功")
        else:
            logger.error(f"FFmpeg命令执行失败: {result.stderr}")

        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        error_msg = f"FFmpeg命令执行超时（{timeout}秒）"
        logger.error(error_msg)
        return False, "", error_msg

    except Exception as e:
        error_msg = f"FFmpeg命令执行异常: {e}"
        logger.error(error_msg)
        return False, "", error_msg


def build_sentence_video_command(
        image_path: str,
        audio_path: str,
        output_path: str,
        subtitle_filter: str,
        gen_setting: dict
) -> List[str]:
    """
    构建单句视频合成命令（电影级效果）

    Args:
        image_path: 图片路径
        audio_path: 音频路径
        output_path: 输出视频路径
        subtitle_filter: 字幕滤镜字符串
        gen_setting: 生成设置

    Returns:
        FFmpeg命令列表
    """
    # 获取音频时长
    duration = get_audio_duration(audio_path)
    if not duration:
        raise ValueError(f"无法获取音频时长: {audio_path}")

    # 解析设置
    resolution = gen_setting.get("resolution", "1440x1080")  # 默认4:3横屏
    fps = gen_setting.get("fps", 30)  # 提高到30fps更流畅
    video_codec = gen_setting.get("video_codec", "libx264")
    audio_codec = gen_setting.get("audio_codec", "aac")
    audio_bitrate = gen_setting.get("audio_bitrate", "192k")

    # 解析分辨率
    width, height = resolution.split('x')
    
    # 计算总帧数
    total_frames = int(fps * duration)

    # 增强的Ken Burns效果：
    # 1. 缩放：从1.0逐渐放大到1.15（更明显的缩放）
    # 2. 平移：从左上角移动到右下角（增加动感）
    # 3. 使用easing函数让动画更自然
    
    # zoompan参数：
    # z: 缩放因子，使用pzoom（前一帧的zoom）+ 增量
    # x, y: 平移坐标
    # d: 持续帧数
    # s: 输出尺寸
    
    if subtitle_filter:
        # 有字幕时的滤镜链
        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"zoompan="
            f"z='min(1+0.00015*on,1.15)':"  # 缩放从1.0到1.15
            f"x='iw/2-(iw/zoom/2)-{int(width)*0.05}*on/{total_frames}':"  # 从左向右平移
            f"y='ih/2-(ih/zoom/2)-{int(height)*0.05}*on/{total_frames}':"  # 从上向下平移
            f"d={total_frames}:"
            f"s={width}x{height}:"
            f"fps={fps}[bg];"
            f"[bg]{subtitle_filter}[v]"
        )
        map_video = "[v]"
    else:
        # 无字幕时的滤镜链
        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"zoompan="
            f"z='min(1+0.00015*on,1.15)':"
            f"x='iw/2-(iw/zoom/2)-{int(width)*0.05}*on/{total_frames}':"
            f"y='ih/2-(ih/zoom/2)-{int(height)*0.05}*on/{total_frames}':"
            f"d={total_frames}:"
            f"s={width}x{height}:"
            f"fps={fps}[v]"
        )
        map_video = "[v]"

    # 构建命令
    command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", str(fps),
        "-i", image_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", map_video,
        "-map", "1:a",
        "-c:v", video_codec,
        "-preset", "slow",  # 使用slow预设获得最佳质量
        "-crf", "20",  # 提高质量（更低的CRF值）
        "-profile:v", "high",  # 使用high profile
        "-level", "4.2",
        "-c:a", audio_codec,
        "-b:a", audio_bitrate,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # 优化网络播放
        "-shortest",
        output_path
    ]

    return command


def concatenate_videos(video_paths: List[Path], output_path: Path, concat_file_path: Path) -> bool:
    """
    拼接多个视频文件

    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频路径
        concat_file_path: concat文件路径

    Returns:
        是否成功
    """
    try:
        # 创建concat文件
        create_concat_file(video_paths, concat_file_path)

        # 构建拼接命令
        command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file_path),
            "-c", "copy",  # 直接复制流，不重新编码
            str(output_path)
        ]

        # 执行命令
        success, stdout, stderr = run_ffmpeg_command(command, timeout=600)

        if success:
            logger.info(f"视频拼接成功: {output_path}")
        else:
            logger.error(f"视频拼接失败: {stderr}")

        return success

    except Exception as e:
        logger.error(f"视频拼接异常: {e}")
        return False


__all__ = [
    "check_ffmpeg_installed",
    "get_audio_duration",
    "create_concat_file",
    "run_ffmpeg_command",
    "build_sentence_video_command",
    "concatenate_videos",
]
