"""
测试单个句子视频生成

使用方法:
python scripts/test_single_sentence_video.py --sentence-id <句子ID>
"""

import asyncio
import sys
from pathlib import Path
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.database import get_async_db
from src.models import Sentence
from src.services.video_synthesis import VideoSynthesisService
from src.core.logging import get_logger
from sqlalchemy import select
import tempfile
import shutil

logger = get_logger(__name__)


async def test_single_sentence(sentence_id: str):
    """
    测试单个句子的视频生成
    
    Args:
        sentence_id: 句子ID
    """
    temp_dir = None
    
    try:
        # 获取数据库会话
        async with get_async_db() as db_session:
            # 查询句子
            result = await db_session.execute(
                select(Sentence).where(Sentence.id == sentence_id)
            )
            sentence = result.scalar_one_or_none()
            
            if not sentence:
                logger.error(f"句子不存在: {sentence_id}")
                return
            
            logger.info(f"找到句子: {sentence.content[:50]}...")
            
            # 检查素材
            if not sentence.image_url:
                logger.error("句子缺少图片素材")
                return
            
            if not sentence.audio_url:
                logger.error("句子缺少音频素材")
                return
            
            logger.info(f"图片: {sentence.image_url}")
            logger.info(f"音频: {sentence.audio_url}")
            
            # 创建临时目录
            temp_dir = Path(tempfile.mkdtemp(prefix="test_video_"))
            logger.info(f"临时目录: {temp_dir}")
            
            # 4:3横屏设置
            gen_setting = {
                "resolution": "1440x1080",  # 4:3横屏
                "fps": 30,
                "video_codec": "libx264",
                "audio_codec": "aac",
                "audio_bitrate": "192k",
                "zoom_speed": 0.0005,
                "subtitle_style": {
                    "font": "Arial",
                    "font_size": 70,  # 漫画解说标准
                    "color": "white",
                    "position": "bottom"
                }
            }
            
            # 创建视频合成服务并设置会话
            video_service = VideoSynthesisService()
            # 手动设置内部会话（绕过属性限制）
            object.__setattr__(video_service, '_db_session', db_session)
            
            # 生成视频
            logger.info("开始生成视频...")
            video_path = await video_service._synthesize_sentence_video(
                sentence=sentence,
                temp_dir=temp_dir,
                index=0,
                gen_setting=gen_setting
            )
            
            # 输出结果
            output_dir = Path("./test_output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"sentence_{sentence_id[:8]}.mp4"
            
            shutil.copy(video_path, output_file)
            
            logger.info(f"✅ 视频生成成功!")
            logger.info(f"📹 输出文件: {output_file.absolute()}")
            logger.info(f"📊 文件大小: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        
    finally:
        # 清理临时目录
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"清理临时目录: {temp_dir}")
            except Exception as e:
                logger.error(f"清理临时目录失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试单个句子视频生成")
    parser.add_argument(
        "--sentence-id",
        required=True,
        help="句子ID (UUID格式)"
    )
    
    args = parser.parse_args()
    
    # 运行测试
    asyncio.run(test_single_sentence(args.sentence_id))


if __name__ == "__main__":
    main()
