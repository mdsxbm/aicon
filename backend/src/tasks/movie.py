"""
电影制作相关的 Celery 任务
"""
from typing import Any, Dict, List
from src.tasks.app import celery_app
from src.tasks.base import async_task_decorator
from src.core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_script"
)
@async_task_decorator
async def movie_generate_script(db_session: AsyncSession, self, chapter_id: str, api_key_id: str, model: str = None):
    """生成剧本的 Celery 任务"""
    from src.services.script_engine import ScriptEngineService
    logger.info(f"Celery任务开始: movie_generate_script (chapter_id={chapter_id})")
    
    async def on_progress(percent, msg):
        self.update_state(state='PROGRESS', meta={'percent': percent, 'message': msg})
        
    service = ScriptEngineService(db_session)
    result = await service.generate_script(chapter_id, api_key_id, model, on_progress=on_progress)
    
    logger.info(f"Celery任务完成: movie_generate_script")
    return {"script_id": str(result.id)}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.produce_shot"
)
@async_task_decorator
async def movie_produce_shot(db_session: AsyncSession, self, shot_id: str, api_key_id: str, model: str = "veo_3_1-fast", force: bool = False):
    """生产单个镜头的 Celery 任务"""
    from src.services.movie_production import MovieProductionService
    logger.info(f"Celery任务开始: movie_produce_shot (shot_id={shot_id}, force={force})")
    
    service = MovieProductionService(db_session)
    task_id = await service.produce_shot_video(shot_id, api_key_id, model, force=force)
    
    logger.info(f"Celery任务提交: Vector Engine Task ID = {task_id}")
    return {"video_task_id": task_id}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.extract_characters"
)
@async_task_decorator
async def movie_extract_characters(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = None):
    """提取角色的 Celery 任务"""
    from src.services.movie_character_service import MovieCharacterService
    logger.info(f"Celery任务开始: movie_extract_characters (script_id={script_id})")
    
    service = MovieCharacterService(db_session)
    chars = await service.extract_characters_from_script(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_extract_characters, extracted {len(chars)} characters")
    return {"character_count": len(chars)}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_character_avatar"
)
@async_task_decorator
async def movie_generate_character_avatar(db_session: AsyncSession, self, character_id: str, api_key_id: str, model: str = None, prompt: str = None, style: str = "cinematic"):
    """生成角色头像的 Celery 任务"""
    from src.services.movie_character_service import MovieCharacterService
    logger.info(f"Celery任务开始: movie_generate_character_avatar (character_id={character_id})")
    
    service = MovieCharacterService(db_session)
    url = await service.generate_character_avatar(character_id, api_key_id, model, prompt, style)
    
    logger.info(f"Celery任务完成: movie_generate_character_avatar")
    return {"avatar_url": url}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_keyframes"
)
@async_task_decorator
async def movie_generate_keyframes(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = None):
    """批量生成关键帧的 Celery 任务"""
    from src.services.visual_identity_service import VisualIdentityService
    logger.info(f"Celery任务开始: movie_generate_keyframes (script_id={script_id})")
    
    service = VisualIdentityService(db_session)
    stats = await service.batch_generate_keyframes(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_generate_keyframes")
    return stats

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.batch_produce_shots"
)
@async_task_decorator
async def movie_batch_produce_shots(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = "veo_3_1-fast"):
    """批量生产镜头的 Celery 任务"""
    from src.services.movie_production import MovieProductionService
    logger.info(f"Celery任务开始: movie_batch_produce_shots (script_id={script_id})")
    
    service = MovieProductionService(db_session)
    stats = await service.batch_produce_shot_videos(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_batch_produce_shots")
    return stats

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.regenerate_keyframe"
)
@async_task_decorator
async def movie_regenerate_keyframe(db_session: AsyncSession, self, shot_id: str, api_key_id: str, model: str = None):
    """重新生成关键帧的 Celery 任务"""
    from src.services.visual_identity_service import VisualIdentityService
    logger.info(f"Celery任务开始: movie_regenerate_keyframe (shot_id={shot_id})")
    
    service = VisualIdentityService(db_session)
    url = await service.regenerate_shot_keyframe(shot_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_regenerate_keyframe")
    return {"first_frame_url": url}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.regenerate_last_frame"
)
@async_task_decorator
async def movie_regenerate_last_frame(db_session: AsyncSession, self, shot_id: str, api_key_id: str, model: str = None):
    """重新生成最后一帧的 Celery 任务"""
    from src.services.visual_identity_service import VisualIdentityService
    logger.info(f"Celery任务开始: movie_regenerate_last_frame (shot_id={shot_id})")
    
    service = VisualIdentityService(db_session)
    url = await service.generate_shot_last_frame(shot_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_regenerate_last_frame")
    return {"last_frame_url": url}

@celery_app.task(name="movie.sync_all_video_task_status")
@async_task_decorator
async def sync_all_video_task_status(db_session: AsyncSession):
    """[Periodic Task] 同步所有处理中的视频任务"""
    from src.services.movie_production import MovieProductionService
    logger.info("Celery定时任务开始: sync_all_video_task_status")
    
    service = MovieProductionService(db_session)
    result = await service.sync_all_video_tasks()
    
    return result

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.batch_generate_avatars"
)
@async_task_decorator
async def movie_batch_generate_avatars(db_session: AsyncSession, self, project_id: str, api_key_id: str, model: str = None):
    """批量生成角色头像的 Celery 任务"""
    from src.services.movie_character_service import MovieCharacterService
    
    logger.info(f"Celery任务开始: movie_batch_generate_avatars (project_id={project_id})")
    
    service = MovieCharacterService(db_session)
    result = await service.batch_generate_avatars(project_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_batch_generate_avatars, 成功: {result['success']}, 失败: {result['failed']}")
    return result
