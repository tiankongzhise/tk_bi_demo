"""数据库管理模块

提供异步数据库连接管理、会话管理和健康检查功能。
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
import logging

from .config import DatabaseConfig
from .exceptions import DatabaseException

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器
    
    负责管理数据库连接、会话和健康检查。
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        if self._initialized:
            logger.warning("数据库已经初始化")
            return
        
        try:
            # 创建异步引擎
            self.engine = create_async_engine(
                self.config.url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_pre_ping=True,  # 连接前检查
                pool_recycle=3600,   # 1小时回收连接
                echo=False,  # 生产环境关闭SQL日志
                future=True
            )
            
            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # 测试连接
            await self.health_check()
            
            self._initialized = True
            logger.info("数据库初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise DatabaseException(f"数据库初始化失败: {e}", error_code=3001)
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")
        self._initialized = False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        使用上下文管理器确保会话正确关闭和事务处理。
        
        Yields:
            AsyncSession: 数据库会话
            
        Raises:
            DatabaseException: 数据库操作异常
        """
        if not self._initialized:
            raise DatabaseException("数据库未初始化", error_code=3001)
        
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise DatabaseException(f"数据库操作失败: {e}", error_code=3002)
        finally:
            await session.close()
    
    async def health_check(self) -> bool:
        """数据库健康检查
        
        Returns:
            bool: 健康状态
        """
        try:
            if not self.engine:
                return False
            
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                return row is not None and row[0] == 1
                
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """获取连接池信息
        
        Returns:
            dict: 连接池状态信息
        """
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
    
    async def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """执行原生SQL
        
        Args:
            sql: SQL语句
            params: 参数字典
            
        Returns:
            list: 查询结果
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            return result.fetchall()


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


async def init_database(config: DatabaseConfig) -> DatabaseManager:
    """初始化数据库管理器
    
    Args:
        config: 数据库配置
        
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()
    
    return _db_manager


def get_database() -> DatabaseManager:
    """获取数据库管理器实例
    
    Returns:
        DatabaseManager: 数据库管理器实例
        
    Raises:
        DatabaseException: 数据库未初始化
    """
    if _db_manager is None:
        raise DatabaseException("数据库未初始化，请先调用init_database", error_code=3001)
    
    return _db_manager


async def close_database() -> None:
    """关闭数据库连接"""
    global _db_manager
    
    if _db_manager:
        await _db_manager.close()
        _db_manager = None