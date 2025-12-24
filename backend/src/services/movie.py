"""
电影服务 - 负责协调电影生成的各个环节
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.movie import MovieScript, MovieScene, MovieShot, MovieCharacter, ScriptStatus
from src.models.chapter import Chapter
from src.core.logging import get_logger
from src.services.base import BaseService
from src.services.keyframe_prompt_builder import KeyframePromptBuilder

logger = get_logger(__name__)

class MovieService(BaseService):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    async def get_script(self, chapter_id: str):
        """获取章节的剧本（包含场景和分镜）"""
        
        # 1. 获取剧本及其关联数据
        stmt = (
            select(MovieScript)
            .join(MovieScript.chapter)
            .where(MovieScript.chapter.has(id=chapter_id))
            .options(
                selectinload(MovieScript.scenes).selectinload(MovieScene.shots),
                joinedload(MovieScript.chapter).joinedload(Chapter.project)
            )
        )
        result = await self.db_session.execute(stmt)
        script = result.scalar_one_or_none()
        
        if not script:
            return None
        
        # 2. 获取项目的所有角色（用于生成提示词）
        project_id = script.chapter.project_id
        stmt_chars = select(MovieCharacter).where(MovieCharacter.project_id == project_id)
        chars_result = await self.db_session.execute(stmt_chars)
        characters = list(chars_result.scalars().all())
        
        # 3. 为每个shot生成专业提示词
        
        for scene in script.scenes:
            for shot in scene.shots:
                # 生成专业提示词并附加到shot对象
                try:
                    prompt = KeyframePromptBuilder.build_prompt(
                        shot=shot,
                        scene=scene,
                        characters=characters,
                        custom_prompt=None
                    )
                    # 动态添加属性（不保存到数据库，仅用于API响应）
                    shot.generated_prompt = prompt
                except Exception as e:
                    logger.error(f"生成shot {shot.id} 提示词失败: {e}")
                    shot.generated_prompt = shot.shot  # 降级为原始描述
        
        return script

    async def get_script_by_id(self, script_id: str) -> Optional[MovieScript]:
        """
        根据ID获取剧本
        """
        stmt = select(MovieScript).where(MovieScript.id == script_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def create_script_task(self, chapter_id: str, api_key_id: str, model: Optional[str] = None):
        """
        创建场景提取任务（新架构：只提取场景，不提取分镜）
        如果已存在剧本，将其删除以避免重复
        """
        # 查找现有剧本
        stmt = select(MovieScript).where(MovieScript.chapter_id == chapter_id)
        result = await self.db_session.execute(stmt)
        existing_script = result.scalars().first()
        
        if existing_script:
            await self.db_session.delete(existing_script)
            await self.db_session.commit()
            logger.info(f"Deleted existing script {existing_script.id} for chapter {chapter_id}")
        
        from src.tasks.movie import movie_extract_scenes
        task = movie_extract_scenes.delay(chapter_id, api_key_id, model)
        return task.id

    async def list_characters(self, project_id: str) -> List[MovieCharacter]:
        """
        获取项目下的所有角色
        """
        stmt = select(MovieCharacter).where(MovieCharacter.project_id == project_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def update_character(self, character_id: str, data: dict) -> Optional[MovieCharacter]:
        """
        更新角色信息
        """
        char = await self.db_session.get(MovieCharacter, character_id)
        if not char:
            return None
            
        if 'avatar_url' in data:
            char.avatar_url = data['avatar_url']
        if 'reference_images' in data:
            char.reference_images = data['reference_images']
            
        await self.db_session.commit()
        await self.db_session.refresh(char)
        return char

    async def delete_character(self, character_id: str) -> bool:
        """
        删除角色
        """
        char = await self.db_session.get(MovieCharacter, character_id)
        if not char:
            return False
            
        await self.db_session.delete(char)
        await self.db_session.commit()
        return True

    async def update_shot(self, shot_id: str, data: dict) -> Optional[MovieShot]:
        """
        更新分镜信息
        """
        shot = await self.db_session.get(MovieShot, shot_id)
        if not shot:
            return None
            
        for key, value in data.items():
            if hasattr(shot, key):
                setattr(shot, key, value)
                
        await self.db_session.commit()
        await self.db_session.refresh(shot)
        return shot

