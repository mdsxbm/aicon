"""
电影分镜相关API路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.api.dependencies import get_current_user_required
from src.api.schemas.movie import StoryboardExtractRequest, KeyframeGenerateRequest

logger = get_logger(__name__)
router = APIRouter()

@router.post("/scripts/{script_id}/extract-shots", summary="从剧本提取分镜")
async def extract_shots(
    script_id: str,
    req: StoryboardExtractRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """从剧本的所有场景提取分镜（异步任务）"""
    from src.tasks.movie import movie_extract_shots
    task = movie_extract_shots.delay(script_id, req.api_key_id, req.model)
    return {"task_id": task.id, "message": "分镜提取任务已提交"}

@router.post("/scripts/{script_id}/generate-keyframes", summary="生成剧本分镜关键帧")
async def generate_keyframes(
    script_id: str,
    req: KeyframeGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """提交剧本分镜关键帧批量生成任务到 Celery"""
    from src.tasks.movie import movie_generate_keyframes
    task = movie_generate_keyframes.delay(script_id, req.api_key_id, req.model)
    return {"task_id": task.id, "message": "分镜关键帧生成任务已提交"}

@router.post("/shots/{shot_id}/generate-keyframe", summary="生成单个分镜关键帧")
async def generate_single_keyframe(
    shot_id: str,
    req: KeyframeGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """提交单个分镜关键帧生成任务到 Celery"""
    from src.tasks.movie import movie_generate_single_keyframe
    task = movie_generate_single_keyframe.delay(shot_id, req.api_key_id, req.model, req.prompt)
    return {"task_id": task.id, "message": "关键帧生成任务已提交"}

@router.post("/scenes/{scene_id}/extract-shots", summary="从单个场景重新提取分镜")
async def extract_single_scene_shots(
    scene_id: str,
    req: StoryboardExtractRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """从单个场景重新提取分镜（先删除现有分镜，异步任务）"""
    from src.tasks.movie import movie_extract_single_scene_shots
    task = movie_extract_single_scene_shots.delay(scene_id, req.api_key_id, req.model)
    return {"task_id": task.id, "message": "单场景分镜提取任务已提交"}
