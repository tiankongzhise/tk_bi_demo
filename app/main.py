"""主应用入口文件

整合所有模块，提供应用启动和管理功能。
"""

import asyncio
import signal
import sys
from typing import Optional
from aiohttp import web
from aiohttp.web import Application

from .core import (
    get_config,
    init_logging,
    get_logger,
    init_database,
    get_database_manager,
    close_database
)
from .services import (
    get_http_client_manager,
    get_task_scheduler
)
from .api import create_app
from .models.database import create_all_tables


class ApplicationManager:
    """应用管理器
    
    负责应用的启动、停止和生命周期管理。
    """
    
    def __init__(self):
        self.app: Optional[Application] = None
        self.logger = None
        self.config = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """初始化应用"""
        try:
            # 加载配置
            self.config = get_config()
            
            # 初始化日志
            init_logging()
            self.logger = get_logger(__name__)
            
            self.logger.info("开始初始化应用...")
            
            # 初始化数据库
            await self._init_database()
            
            # 初始化HTTP客户端
            await self._init_http_clients()
            
            # 初始化任务调度器
            await self._init_task_scheduler()
            
            # 创建Web应用
            self.app = create_app()
            
            # 设置应用生命周期事件
            self.app.on_startup.append(self._on_startup)
            self.app.on_cleanup.append(self._on_cleanup)
            
            self.logger.info("应用初始化完成")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"应用初始化失败: {str(e)}", exc_info=True)
            else:
                print(f"应用初始化失败: {str(e)}")
            raise
    
    async def _init_database(self) -> None:
        """初始化数据库"""
        self.logger.info("初始化数据库连接...")
        
        # 初始化数据库管理器
        await init_database()
        
        # 创建数据库表
        await create_all_tables()
        
        # 测试数据库连接
        db_manager = get_database_manager()
        if await db_manager.health_check():
            self.logger.info("数据库连接正常")
        else:
            raise Exception("数据库连接失败")
    
    async def _init_http_clients(self) -> None:
        """初始化HTTP客户端"""
        self.logger.info("初始化HTTP客户端...")
        
        http_manager = get_http_client_manager()
        
        # 为每个平台创建HTTP客户端
        platforms = ['baidu', 'sogou', 'qihoo', 'shenma', 'bytedance', 'tencent']
        for platform in platforms:
            await http_manager.get_client(platform)
        
        self.logger.info(f"HTTP客户端初始化完成，共创建 {len(http_manager.clients)} 个客户端")
    
    async def _init_task_scheduler(self) -> None:
        """初始化任务调度器"""
        self.logger.info("初始化任务调度器...")
        
        scheduler = get_task_scheduler()
        await scheduler.start()
        
        self.logger.info("任务调度器启动完成")
    
    async def _on_startup(self, app: Application) -> None:
        """应用启动事件处理
        
        Args:
            app: aiohttp应用实例
        """
        self.logger.info("Web应用启动中...")
        
        # 可以在这里添加启动时需要执行的任务
        # 例如：预热缓存、启动定时任务等
        
        self.logger.info("Web应用启动完成")
    
    async def _on_cleanup(self, app: Application) -> None:
        """应用清理事件处理
        
        Args:
            app: aiohttp应用实例
        """
        self.logger.info("开始清理应用资源...")
        
        try:
            # 停止任务调度器
            scheduler = get_task_scheduler()
            await scheduler.stop()
            self.logger.info("任务调度器已停止")
            
            # 关闭HTTP客户端
            http_manager = get_http_client_manager()
            await http_manager.close_all()
            self.logger.info("HTTP客户端已关闭")
            
            # 关闭数据库连接
            await close_database()
            self.logger.info("数据库连接已关闭")
            
            self.logger.info("应用资源清理完成")
        
        except Exception as e:
            self.logger.error(f"应用资源清理失败: {str(e)}", exc_info=True)
    
    async def run(self, host: str = None, port: int = None) -> None:
        """运行应用
        
        Args:
            host: 监听主机，默认从配置读取
            port: 监听端口，默认从配置读取
        """
        if not self.app:
            raise RuntimeError("应用未初始化，请先调用 initialize()")
        
        # 从配置获取默认值
        if host is None:
            host = getattr(self.config, 'HOST', '0.0.0.0')
        if port is None:
            port = getattr(self.config, 'PORT', 8000)
        
        self.logger.info(f"启动Web服务器: http://{host}:{port}")
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        try:
            # 创建服务器
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, host, port)
            await site.start()
            
            self.logger.info(f"Web服务器启动成功，监听 {host}:{port}")
            
            # 等待关闭信号
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Web服务器启动失败: {str(e)}", exc_info=True)
            raise
        
        finally:
            self.logger.info("正在关闭Web服务器...")
            await runner.cleanup()
            self.logger.info("Web服务器已关闭")
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"接收到信号 {signum}，开始优雅关闭...")
            asyncio.create_task(self._graceful_shutdown())
        
        # 注册信号处理器
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        else:
            # Windows下只支持SIGINT
            signal.signal(signal.SIGINT, signal_handler)
    
    async def _graceful_shutdown(self) -> None:
        """优雅关闭"""
        self.logger.info("开始优雅关闭应用...")
        
        # 设置关闭事件
        self._shutdown_event.set()
        
        # 给正在处理的请求一些时间完成
        await asyncio.sleep(1)
        
        self.logger.info("应用关闭完成")
    
    async def stop(self) -> None:
        """停止应用"""
        await self._graceful_shutdown()


# 全局应用管理器实例
_app_manager: Optional[ApplicationManager] = None


def get_app_manager() -> ApplicationManager:
    """获取应用管理器实例
    
    Returns:
        ApplicationManager: 应用管理器实例
    """
    global _app_manager
    if _app_manager is None:
        _app_manager = ApplicationManager()
    return _app_manager


async def create_application() -> Application:
    """创建应用实例
    
    Returns:
        Application: aiohttp应用实例
    """
    app_manager = get_app_manager()
    await app_manager.initialize()
    return app_manager.app


async def run_application(host: str = None, port: int = None) -> None:
    """运行应用
    
    Args:
        host: 监听主机
        port: 监听端口
    """
    app_manager = get_app_manager()
    await app_manager.initialize()
    await app_manager.run(host, port)


def main() -> None:
    """主函数"""
    try:
        # 运行应用
        asyncio.run(run_application())
    except KeyboardInterrupt:
        print("\n应用被用户中断")
    except Exception as e:
        print(f"应用运行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()