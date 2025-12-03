from src.core.logging import get_logger
from src.services.base import SessionManagedService

logger = get_logger(__name__)


# ============================================================
# VideoService 主体
# ============================================================

class VideoService(SessionManagedService):
    pass


video_service = VideoService()
__all__ = ["VideoService", "video_service"]

if __name__ == "__main__":
    import asyncio


    async def test():
        service = VideoService()


    asyncio.run(test())
