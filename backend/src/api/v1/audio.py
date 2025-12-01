"""
音频生成 API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.audio import AudioGenerateRequest, AudioGenerateResponse
from src.core.database import get_db
from src.core.exceptions import NotFoundError, BusinessLogicError
from src.core.logging import get_logger
from src.models.chapter import Chapter
from src.models.user import User
from src.tasks.task import generate_audio

logger = get_logger(__name__)

router = APIRouter()


@router.post("/generate-audio", response_model=AudioGenerateResponse)
async def generate_audio_api(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        request: AudioGenerateRequest
):
    """
    批量生成音频
    
    根据句子ID列表，调用AI音频生成服务生成音频。
    适合批量生成和重新生成音频场景。
    """
    from sqlalchemy import select
    from src.models.sentence import Sentence
    from src.models.paragraph import Paragraph

    # 1. 验证句子权限和状态
    if not request.sentences_ids:
        raise BusinessLogicError(message="句子ID列表不能为空")

    # 2. 获取句子并验证权限
    stmt = select(Sentence).join(Paragraph).join(Chapter).where(
        Sentence.id.in_(request.sentences_ids)
    )
    result = await db.execute(stmt)
    sentences = result.scalars().all()

    if len(sentences) != len(request.sentences_ids):
        raise NotFoundError(
            "部分句子不存在",
            resource_type="sentence"
        )

    # 3. 投递任务到celery
    sentence_ids_hex = [sentence_id.hex for sentence_id in request.sentences_ids]
    result = generate_audio.delay(
        request.api_key_id.hex, 
        sentence_ids_hex,
        voice=request.voice,
        model=request.model
    )

    logger.info(f"成功为句子列表 {request.sentences_ids} 投递音频生成任务，任务ID: {result.id}")
    return AudioGenerateResponse(success=True, message="音频生成任务已提交", task_id=result.id)


__all__ = ["router"]
