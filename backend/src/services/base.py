"""
服务基类 - 提供统一的数据库会话管理和基础功能（修复版）
"""

from typing import Optional, TYPE_CHECKING, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.core.logging import get_logger

logger = get_logger(__name__)


# ================================================================
#   基础服务（不再自动创建 Session，必须显式传入）
# ================================================================
class BaseService:
    """
    服务基类（修复版）

    - 不再自动创建数据库会话，避免隐式事务和连接泄漏
    - 如果没有传入会话，直接报错
    - 由 FastAPI DI 或 SessionManagedService 负责会话创建
    """

    def __init__(self, db_session: Optional[AsyncSession]):
        """
        初始化服务实例
        Args:
            db_session: 外部传入的 SQLAlchemy AsyncSession
        """
        self._db_session = db_session

    # ------------------------------------------------------------------
    #   Session getter
    # ------------------------------------------------------------------
    @property
    def db_session(self) -> AsyncSession:
        """获取数据库会话"""
        if self._db_session is None:
            raise RuntimeError(
                f"{self.__class__.__name__}: 无可用数据库会话。"
                f"必须通过依赖注入或 SessionManagedService 创建会话。"
            )
        return self._db_session

    # ------------------------------------------------------------------
    #   事务控制
    # ------------------------------------------------------------------
    async def commit(self):
        """提交事务"""
        try:
            await self.db_session.commit()
            logger.debug(f"{self.__class__.__name__} 提交事务成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 提交事务失败: {e}")
            await self.rollback()
            raise

    async def rollback(self):
        """回滚事务"""
        try:
            await self.db_session.rollback()
            logger.debug(f"{self.__class__.__name__} 回滚事务成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 回滚事务失败: {e}")

    async def flush(self):
        """刷新会话"""
        try:
            await self.db_session.flush()
            logger.debug(f"{self.__class__.__name__} 刷新会话成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 刷新会话失败: {e}")
            await self.rollback()
            raise

    async def refresh(self, obj):
        """刷新对象"""
        try:
            await self.db_session.refresh(obj)
            logger.debug(f"{self.__class__.__name__} 刷新对象成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 刷新对象失败: {e}")
            raise

    async def execute(self, query, params: Optional[Dict[str, Any]] = None):
        """
        执行 SQLAlchemy 查询
        """
        return await self.db_session.execute(query, params=params)

    # ------------------------------------------------------------------
    #   CRUD 便捷方法
    # ------------------------------------------------------------------
    async def add(self, obj):
        """添加对象到会话（同步方法）"""
        await self.db_session.add(obj)
        logger.debug(f"{self.__class__.__name__} 添加对象到会话")

    async def delete(self, obj):
        """删除对象"""
        await self.db_session.delete(obj)
        logger.debug(f"{self.__class__.__name__} 从会话中删除对象")

    async def get(self, model_class, identifier):
        """根据主键获取对象"""
        return await self.db_session.get(model_class, identifier)


# ================================================================
#   自主管理会话的服务类（适用于脚本 / 后台任务）
# ================================================================
class SessionManagedService(BaseService):
    """
    自管理数据库会话的服务类，适用于后台任务、脚本等。
    """

    def __init__(self):
        super().__init__(db_session=None)
        self._session_ctx = None

    async def __aenter__(self):
        """
        创建会话上下文
        """
        from contextlib import asynccontextmanager

        # 正确包装 get_async_db（避免 async generator 不能 __aenter__）
        @asynccontextmanager
        async def session_wrapper():
            async with AsyncSessionLocal() as session:
                yield session

        self._session_ctx = session_wrapper()
        self._db_session = await self._session_ctx.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文，提交或回滚事务 + 关闭会话
        """
        if exc_type:
            await self.rollback()

        if self._session_ctx:
            await self._session_ctx.__aexit__(exc_type, exc_val, exc_tb)

        self._db_session = None
        self._session_ctx = None


__all__ = [
    "BaseService",
    "SessionManagedService",
]
