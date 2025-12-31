"""
FFmpeg工具函数 - 视频处理相关的FFmpeg操作
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)


import shutil

# 全局缓存 FFmpeg 检查结果
_ffmpeg_installed_cache = None

def check_ffmpeg_installed() -> bool:
    """
    检查FFmpeg是否已安装

    Returns:
        如果FFmpeg可用返回True，否则返回False
    """
    global _ffmpeg_installed_cache
    
    # 1. 检查缓存
    if _ffmpeg_installed_cache is not None:
        return _ffmpeg_installed_cache

    # 2. 初步使用 shutil.which 检查命令是否存在
    if not shutil.which("ffmpeg"):
        logger.error("FFmpeg命令未找到，请确保已安装并加入PATH")
        _ffmpeg_installed_cache = False
        return False

    # 3. 运行 ffmpeg -version 验证（增加超时时间）
    try:
        logger.info("正在验证 FFmpeg 安装情况...")
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=20  # 从5s增加到20s，应对系统高负载
        )
        
        if result.returncode == 0:
            logger.info("FFmpeg已安装并可用")
            _ffmpeg_installed_cache = True
            return True
        else:
            logger.error(f"FFmpeg验证失败，返回码: {result.returncode}")
            _ffmpeg_installed_cache = False
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg检查超时（20秒），可能是系统负载过高，暂时假设已安装")
        # 如果超时但 shutil.which 过了，可能只是运行慢，返回 True 以避免阻塞业务
        # 但我们不记录缓存，下次可能还需要重新检查，或者记录为 True 减少后续干扰
        _ffmpeg_installed_cache = True 
        return True
    except Exception as e:
        logger.error(f"FFmpeg检查异常: {e}")
        _ffmpeg_installed_cache = False
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


def get_video_fps(video_path: str) -> Optional[float]:
    """
    获取视频帧率

    Args:
        video_path: 视频文件路径

    Returns:
        视频帧率（fps），如果失败返回None
    """
    try:
        # 使用ffprobe获取视频帧率
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # 帧率格式为 "30/1" 或 "30000/1001"
            fps_str = result.stdout.strip()
            if '/' in fps_str:
                num, den = fps_str.split('/')
                fps = float(num) / float(den)
            else:
                fps = float(fps_str)
            
            logger.debug(f"视频帧率: {video_path} = {fps:.2f}fps")
            return fps
        else:
            logger.error(f"获取视频帧率失败: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"获取视频帧率异常: {e}")
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
    zoom_speed = gen_setting.get("zoom_speed", 0.00015)  # Ken Burns缩放速度，默认0.00015

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
    
    # 构建视频滤镜链
    video_filters = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        f"zoompan="
        f"z='min(1+{zoom_speed}*on,1.15)':"  # 使用配置的缩放速度
        f"x='iw/2-(iw/zoom/2)-{int(width)*0.05}*on/{total_frames}':"  # 从左向右平移
        f"y='ih/2-(ih/zoom/2)-{int(height)*0.05}*on/{total_frames}':"  # 从上向下平移
        f"d={total_frames}:"
        f"s={width}x{height}:"
        f"fps={fps}"
    )
    
    if subtitle_filter:
        # 有字幕时的滤镜链
        filter_complex = (
            f"{video_filters}[bg];"
            f"[bg]{subtitle_filter}[v]"
        )
        map_video = "[v]"
    else:
        # 无字幕时的滤镜链
        filter_complex = f"{video_filters}[v]"
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


def concatenate_videos(
    video_paths: List[Path], 
    output_path: Path, 
    concat_file_path: Path,
    # 新参数: 拼接模式
    mode: str = "crossfade",
    # crossfade模式参数
    transition_type: str = "fade",
    transition_duration: float = 0.5,
    # trim模式参数(保留向后兼容)
    remove_duplicate_frames: bool = False,
    trim_frames: int = 35
) -> bool:
    """
    拼接多个视频文件,支持多种拼接模式
    
    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频路径
        concat_file_path: concat文件路径(用于fallback)
        mode: 拼接模式, 可选:
            - "crossfade": 使用交叉淡化过渡(推荐,最自然)
            - "trim": 裁剪重复帧
            - "fast": 快速拼接(不处理重复帧)
        transition_type: 过渡效果类型(仅crossfade模式), 可选:
            - "fade": 淡入淡出(默认,最自然)
            - "dissolve": 溶解
            - "wipeleft", "wiperight": 左右擦除
            - "slideleft", "slideright": 左右滑动
            - "circleopen", "circleclose": 圆形开合
            - "fadeblack", "fadewhite": 黑/白场过渡
            等30+种效果
        transition_duration: 过渡时长(秒), 默认0.5秒
        remove_duplicate_frames: 是否去除重复帧(trim模式,已废弃)
        trim_frames: 裁剪帧数(trim模式,已废弃)
    
    Returns:
        是否成功
    """
    try:
        if len(video_paths) == 0:
            logger.error("视频路径列表为空")
            return False
        
        if len(video_paths) == 1:
            # 只有一个视频,直接复制
            import shutil
            shutil.copy2(video_paths[0], output_path)
            logger.info(f"只有一个视频,直接复制: {output_path}")
            return True
        
        # 根据模式选择拼接方法
        if mode == "crossfade":
            return _concatenate_with_xfade(
                video_paths, output_path, 
                transition_type, transition_duration
            )
        elif mode == "trim" or remove_duplicate_frames:
            return _concatenate_with_trim(
                video_paths, output_path, 
                concat_file_path, trim_frames
            )
        else:  # mode == "fast"
            return _concatenate_videos_fast(
                video_paths, output_path, concat_file_path
            )
    
    except Exception as e:
        logger.error(f"视频拼接异常: {e}", exc_info=True)
        # Fallback到快速方法
        try:
            logger.warning("尝试使用快速方法(不去除重复帧)...")
            return _concatenate_videos_fast(video_paths, output_path, concat_file_path)
        except Exception as fallback_error:
            logger.error(f"快速方法也失败: {fallback_error}")
            return False


def _concatenate_with_xfade(
    video_paths: List[Path],
    output_path: Path,
    transition_type: str = "fade",
    transition_duration: float = 0.5
) -> bool:
    """
    使用交叉淡化效果拼接视频(推荐方法)
    
    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频路径
        transition_type: 过渡效果类型
        transition_duration: 过渡时长(秒)
    
    Returns:
        是否成功
    """
    try:
        logger.info(f"开始拼接 {len(video_paths)} 个视频(crossfade模式)")
        logger.info(f"过渡效果: {transition_type}, 过渡时长: {transition_duration}秒")
        
        # 获取每个视频的时长
        durations = []
        for video_path in video_paths:
            duration = get_audio_duration(str(video_path))
            if not duration:
                logger.error(f"无法获取视频时长: {video_path}")
                return False
            durations.append(duration)
            logger.debug(f"视频 {video_path.name}: {duration:.2f}秒")
        
        # 构建xfade滤镜链 (仅处理视频)
        video_filter_parts = []
        
        # 第一个视频作为基础
        current_video_label = "[0:v]"
        offset = 0.0
        
        for i in range(1, len(video_paths)):
            # 计算offset: 前一个视频的累计时长 - 过渡时长
            offset += durations[i-1] - transition_duration
            
            # 构建xfade视频滤镜
            output_video_label = f"[v{i}out]" if i < len(video_paths) - 1 else "[vout]"
            xfade_filter = (
                f"{current_video_label}[{i}:v]"
                f"xfade=transition={transition_type}:"
                f"duration={transition_duration}:"
                f"offset={offset:.3f}"
                f"{output_video_label}"
            )
            video_filter_parts.append(xfade_filter)
            current_video_label = output_video_label
        
        # 音频处理: 使用简单的concat滤镜
        # 为每个音频流添加延迟以匹配视频过渡
        audio_filter_parts = []
        
        for i in range(len(video_paths)):
            if i == 0:
                # 第一个音频: 裁剪结尾的过渡时长
                trim_end = durations[i] - transition_duration if i < len(video_paths) - 1 else durations[i]
                audio_filter_parts.append(f"[{i}:a]atrim=0:{trim_end},asetpts=PTS-STARTPTS[a{i}]")
            elif i == len(video_paths) - 1:
                # 最后一个音频: 跳过开头的过渡时长
                audio_filter_parts.append(f"[{i}:a]atrim={transition_duration},asetpts=PTS-STARTPTS[a{i}]")
            else:
                # 中间的音频: 跳过开头和裁剪结尾
                trim_end = durations[i] - transition_duration
                audio_filter_parts.append(
                    f"[{i}:a]atrim={transition_duration}:{trim_end},asetpts=PTS-STARTPTS[a{i}]"
                )
        
        # 拼接所有音频
        audio_inputs = ''.join([f"[a{i}]" for i in range(len(video_paths))])
        audio_concat = f"{audio_inputs}concat=n={len(video_paths)}:v=0:a=1[aout]"
        audio_filter_parts.append(audio_concat)
        
        # 组合视频和音频滤镜
        filter_complex = ";".join(video_filter_parts + audio_filter_parts)
        
        logger.debug(f"Filter complex: {filter_complex}")
        
        # 构建FFmpeg命令
        command = ["ffmpeg", "-y"]
        
        # 添加所有输入文件
        for video_path in video_paths:
            command.extend(["-i", str(video_path)])
        
        # 添加滤镜和输出参数
        command.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",  # 高质量
            "-pix_fmt", "yuv420p",  # 确保兼容性
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",  # 音频采样率
            "-movflags", "+faststart",
            str(output_path)
        ])
        
        # 执行命令
        success, stdout, stderr = run_ffmpeg_command(command, timeout=600)
        
        if success:
            logger.info(f"✅ 视频拼接成功(crossfade模式): {output_path}")
            return True
        else:
            logger.error(f"❌ 视频拼接失败: {stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Crossfade拼接异常: {e}", exc_info=True)
        return False


def _concatenate_with_trim(
    video_paths: List[Path],
    output_path: Path,
    concat_file_path: Path,
    trim_frames: int = 35
) -> bool:
    """
    使用帧裁剪方式拼接视频(旧方法,保留兼容性)
    
    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频路径
        concat_file_path: concat文件路径
        trim_frames: 裁剪帧数
    
    Returns:
        是否成功
    """
    try:
        logger.info(f"开始拼接 {len(video_paths)} 个视频(trim模式,裁剪开头{trim_frames}帧)")
        
        # 获取第一个视频的帧率
        fps = get_video_fps(str(video_paths[0]))
        if not fps:
            logger.warning("无法获取视频帧率,使用默认值30fps")
            fps = 30.0
        
        # 计算每帧的时长(秒)
        frame_duration = 1.0 / fps
        logger.info(f"视频帧率: {fps:.2f}fps, 每帧时长: {frame_duration:.4f}秒, 裁剪{trim_frames}帧={trim_frames*frame_duration:.4f}秒")
        
        # 构建filter_complex
        video_filters = []
        audio_filters = []
        
        for idx, video_path in enumerate(video_paths):
            if idx == 0:
                # 第一个视频保持完整
                video_filters.append(f"[{idx}:v]null[v{idx}]")
                audio_filters.append(f"[{idx}:a]anull[a{idx}]")
            else:
                # 后续视频去掉前N帧
                duration = get_audio_duration(str(video_path))
                if duration:
                    total_frames = int(duration * fps)
                    if total_frames <= trim_frames:
                        logger.warning(f"视频{idx}总帧数({total_frames})不足以裁剪{trim_frames}帧,跳过裁剪")
                        video_filters.append(f"[{idx}:v]null[v{idx}]")
                        audio_filters.append(f"[{idx}:a]anull[a{idx}]")
                        continue
                
                # trim: start_frame=N 表示从第N帧开始(跳过前N帧)
                video_filters.append(f"[{idx}:v]trim=start_frame={trim_frames},setpts=PTS-STARTPTS[v{idx}]")
                # atrim: start=N*frame_duration 表示跳过前N帧的音频
                start_time = trim_frames * frame_duration
                audio_filters.append(f"[{idx}:a]atrim=start={start_time},asetpts=PTS-STARTPTS[a{idx}]")
        
        # 拼接所有处理后的流
        video_inputs = ''.join([f"[v{i}]" for i in range(len(video_paths))])
        audio_inputs = ''.join([f"[a{i}]" for i in range(len(video_paths))])
        
        video_concat = f"{video_inputs}concat=n={len(video_paths)}:v=1:a=0[outv]"
        audio_concat = f"{audio_inputs}concat=n={len(video_paths)}:v=0:a=1[outa]"
        
        # 组合完整的filter_complex
        filter_complex = ';'.join(video_filters + audio_filters + [video_concat, audio_concat])
        
        # 构建FFmpeg命令
        command = ["ffmpeg", "-y"]
        
        # 添加所有输入文件
        for video_path in video_paths:
            command.extend(["-i", str(video_path)])
        
        # 添加滤镜和输出参数
        command.extend([
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ])
        
        # 执行命令
        success, stdout, stderr = run_ffmpeg_command(command, timeout=600)
        
        if success:
            logger.info(f"✅ 视频拼接成功(trim模式): {output_path}")
            return True
        else:
            logger.error(f"❌ 视频拼接失败: {stderr}")
            # Fallback到快速方法
            logger.warning("尝试使用快速方法...")
            return _concatenate_videos_fast(video_paths, output_path, concat_file_path)
    
    except Exception as e:
        logger.error(f"Trim拼接异常: {e}", exc_info=True)
        return False


def _concatenate_videos_fast(video_paths: List[Path], output_path: Path, concat_file_path: Path) -> bool:
    """
    快速拼接视频(不去除重复帧)
    
    使用 -c copy 直接复制流,速度快但会保留重复帧
    
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
            logger.info(f"视频拼接成功(快速模式): {output_path}")
        else:
            logger.error(f"视频拼接失败: {stderr}")

        return success

    except Exception as e:
        logger.error(f"视频拼接异常: {e}")
        return False



def mix_bgm_with_video(
        video_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.15,
        loop_bgm: bool = True
) -> bool:
    """
    将BGM混合到视频中

    Args:
        video_path: 输入视频路径
        bgm_path: BGM音频路径
        output_path: 输出视频路径
        bgm_volume: BGM音量（0.0-1.0），默认0.15（15%）
        loop_bgm: 是否循环BGM以匹配视频长度

    Returns:
        是否成功
    """
    try:
        # 获取视频时长
        video_duration = get_audio_duration(video_path)
        if not video_duration:
            logger.error("无法获取视频时长")
            return False

        # 获取BGM时长
        bgm_duration = get_audio_duration(bgm_path)
        if not bgm_duration:
            logger.error("无法获取BGM时长")
            return False

        logger.info(f"视频时长: {video_duration:.2f}s, BGM时长: {bgm_duration:.2f}s, BGM音量: {bgm_volume}")

        # 构建FFmpeg命令
        # 使用 amix 滤镜混合原音频和BGM
        # 如果BGM较短，使用 aloop 循环；如果较长，会自动截断
        
        if loop_bgm and bgm_duration < video_duration:
            # 计算需要循环的次数
            loop_count = int(video_duration / bgm_duration) + 1
            
            # 构建滤镜：调整BGM音量，循环BGM，然后与原音频混合
            filter_complex = (
                f"[1:a]volume={bgm_volume},aloop=loop={loop_count}:size=2e+09[bgm];"
                f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
        else:
            # BGM足够长或不需要循环，直接混合
            filter_complex = (
                f"[1:a]volume={bgm_volume}[bgm];"
                f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )

        command = [
            "ffmpeg",
            "-y",
            "-i", video_path,  # 输入视频
            "-i", bgm_path,    # 输入BGM
            "-filter_complex", filter_complex,
            "-map", "0:v",     # 使用视频流
            "-map", "[aout]",  # 使用混合后的音频流
            "-c:v", "copy",    # 视频流直接复制，不重新编码
            "-c:a", "aac",     # 音频编码为AAC
            "-b:a", "192k",    # 音频比特率
            "-shortest",       # 以最短的流为准
            output_path
        ]

        # 执行命令
        success, stdout, stderr = run_ffmpeg_command(command, timeout=600)

        if success:
            logger.info(f"BGM混合成功: {output_path}")
        else:
            logger.error(f"BGM混合失败: {stderr}")

        return success

    except Exception as e:
        logger.error(f"BGM混合异常: {e}")
        return False




def apply_video_speed(
        input_path: str,
        output_path: str,
        speed: float = 1.0
) -> bool:
    """
    对整个视频应用速度调整

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        speed: 播放速度（0.5-2.0），默认1.0（正常速度）

    Returns:
        是否成功
    """
    try:
        if speed == 1.0:
            # 速度为1.0时，直接复制文件
            import shutil
            shutil.copy2(input_path, output_path)
            logger.info(f"视频速度为1.0，直接复制文件")
            return True

        logger.info(f"开始应用视频速度: {speed}x")

        # 构建视频滤镜 - setpts调整视频时间戳
        video_filter = f"setpts=PTS/{speed}"

        # 构建音频滤镜 - atempo调整音频速度并保持音调
        # atempo的范围是0.5-2.0，如果需要更大的速度变化，需要链式调用
        audio_filters = []
        remaining_speed = speed

        while remaining_speed > 2.0:
            audio_filters.append("atempo=2.0")
            remaining_speed /= 2.0

        while remaining_speed < 0.5:
            audio_filters.append("atempo=0.5")
            remaining_speed /= 0.5

        if remaining_speed != 1.0:
            audio_filters.append(f"atempo={remaining_speed}")

        audio_filter = ",".join(audio_filters) if audio_filters else "anull"

        # 构建FFmpeg命令
        command = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-filter:v", video_filter,
            "-filter:a", audio_filter,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

        # 执行命令
        success, stdout, stderr = run_ffmpeg_command(command, timeout=600)

        if success:
            logger.info(f"视频速度调整成功: {speed}x, 输出={output_path}")
        else:
            logger.error(f"视频速度调整失败: {stderr}")

        return success

    except Exception as e:
        logger.error(f"视频速度调整异常: {e}")
        return False


__all__ = [
    "check_ffmpeg_installed",
    "get_audio_duration",
    "get_video_fps",
    "create_concat_file",
    "run_ffmpeg_command",
    "build_sentence_video_command",
    "concatenate_videos",
    "apply_video_speed",
    "mix_bgm_with_video",
]

