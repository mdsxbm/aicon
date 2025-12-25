"""
电影角色相关API路由
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.api.dependencies import get_current_user_required
from src.services.movie_character_service import MovieCharacterService
from src.api.schemas.movie import (
    MovieCharacterBase,
    CharacterExtractRequest,
    CharacterUpdateRequest,
    CharacterGenerateRequest,
    BatchGenerateAvatarsRequest
)

logger = get_logger(__name__)
router = APIRouter()

@router.post("/chapters/{chapter_id}/extract-characters", summary="从章节提取角色")
async def extract_characters(
    chapter_id: str, 
    req: CharacterExtractRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """从章节内容中提取角色（异步任务）"""
    from src.tasks.movie import movie_extract_characters
    task = movie_extract_characters.delay(chapter_id, req.api_key_id, req.model)
    return {"task_id": task.id, "message": "角色提取任务已提交"}

@router.get("/projects/{project_id}/characters")
async def list_characters(
    project_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """列出项目下的所有电影角色"""
    from src.services.movie import MovieService
    from src.api.schemas.movie import MovieCharacterBase
    
    movie_service = MovieService(db)
    chars = await movie_service.list_characters(project_id)
    
    # 使用schema的from_orm_with_signed_urls方法
    result = [MovieCharacterBase.from_orm_with_signed_urls(char) for char in chars]
    
    # 返回统一格式：{ characters: [...] }
    return {"characters": [r.model_dump() for r in result]}

@router.put("/characters/{character_id}", response_model=MovieCharacterBase)
async def update_character(
    character_id: str,
    req: CharacterUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """更新角色信息（头像、参考图）"""
    from src.services.movie import MovieService
    movie_service = MovieService(db)
    updated_char = await movie_service.update_character(character_id, req.dict(exclude_unset=True))
    if not updated_char:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated_char

@router.delete("/characters/{character_id}", summary="删除角色")
async def delete_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """删除角色"""
    from src.services.movie import MovieService
    movie_service = MovieService(db)
    success = await movie_service.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"success": True, "message": "角色已删除"}

@router.post("/characters/{character_id}/generate", summary="生成角色头像")
async def generate_character_avatar(
    character_id: str,
    req: CharacterGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """提交角色头像生成任务到 Celery"""
    from src.tasks.movie import movie_generate_character_avatar
    task = movie_generate_character_avatar.delay(character_id, req.api_key_id, req.model, req.prompt, req.style)
    return {"task_id": task.id, "message": "角色头像生成任务已提交"}

@router.post("/projects/{project_id}/characters/batch-generate", summary="批量生成角色定妆照")
async def batch_generate_avatars(
    project_id: str,
    req: BatchGenerateAvatarsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """批量为所有未生成定妆照的角色生成头像"""
    from src.tasks.movie import movie_batch_generate_avatars
    task = movie_batch_generate_avatars.delay(project_id, req.api_key_id, req.model)
    return {"task_id": task.id, "message": "批量生成定妆照任务已提交"}
