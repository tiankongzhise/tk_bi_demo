"""日志配置模块

提供结构化日志和统一的日志管理功能。
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from structlog.stdlib import LoggerFactory

from .config import LogConfig


class JSONFormatter(logging.Formatter):
    """JSON格式化器
    
    将日志记录格式化为JSON格式，便于日志分析和处理。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            str: JSON格式的日志字符串
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """结构化格式化器
    
    提供人类可读的结构化日志格式。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        # 基础格式
        base_format = (
            f"{timestamp} | {record.levelname:8} | "
            f"{record.name}:{record.lineno} | {record.getMessage()}"
        )
        
        # 添加异常信息
        if record.exc_info:
            base_format += f"\n{self.formatException(record.exc_info)}"
        
        return base_format


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器
    
    为日志记录添加上下文信息。
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """处理日志消息
        
        Args:
            msg: 日志消息
            kwargs: 关键字参数
            
        Returns:
            tuple: (消息, 关键字参数)
        """
        # 将extra信息合并到日志记录中
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        kwargs["extra"].update(self.extra)
        kwargs["extra"]["extra_data"] = self.extra
        
        return msg, kwargs


class LogManager:
    """日志管理器
    
    统一管理应用的日志配置和记录器。
    """
    
    def __init__(self, config: LogConfig):
        self.config = config
        self._initialized = False
        self._loggers: Dict[str, logging.Logger] = {}
    
    def initialize(self) -> None:
        """初始化日志系统"""
        if self._initialized:
            return
        
        # 创建日志目录
        log_path = Path(self.config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if self.config.format.lower() == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(StructuredFormatter())
        
        root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = self._create_file_handler()
        root_logger.addHandler(file_handler)
        
        # 配置structlog
        self._configure_structlog()
        
        self._initialized = True
        
        # 记录初始化完成
        logger = self.get_logger("log_manager")
        logger.info("日志系统初始化完成", extra={"config": self.config.dict()})
    
    def _create_file_handler(self) -> logging.Handler:
        """创建文件处理器"""
        # 解析文件大小
        max_bytes = self._parse_size(self.config.max_size)
        
        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.config.file_path,
            maxBytes=max_bytes,
            backupCount=self.config.backup_count,
            encoding="utf-8"
        )
        
        file_handler.setLevel(getattr(logging, self.config.level.upper()))
        
        if self.config.format.lower() == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(StructuredFormatter())
        
        return file_handler
    
    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串
        
        Args:
            size_str: 大小字符串，如 "100MB", "1GB"
            
        Returns:
            int: 字节数
        """
        size_str = size_str.upper().strip()
        
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _configure_structlog(self) -> None:
        """配置structlog"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def get_logger(
        self, 
        name: str, 
        extra_context: Optional[Dict[str, Any]] = None
    ) -> LoggerAdapter:
        """获取日志记录器
        
        Args:
            name: 记录器名称
            extra_context: 额外上下文信息
            
        Returns:
            LoggerAdapter: 日志适配器
        """
        if not self._initialized:
            self.initialize()
        
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        logger = self._loggers[name]
        context = extra_context or {}
        
        return LoggerAdapter(logger, context)
    
    def get_structlog_logger(self, name: str) -> structlog.BoundLogger:
        """获取structlog记录器
        
        Args:
            name: 记录器名称
            
        Returns:
            structlog.BoundLogger: structlog记录器
        """
        if not self._initialized:
            self.initialize()
        
        return structlog.get_logger(name)
    
    def set_level(self, level: str) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        log_level = getattr(logging, level.upper())
        logging.getLogger().setLevel(log_level)
        
        # 更新所有处理器的级别
        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)
    
    def add_context_filter(self, filter_func) -> None:
        """添加上下文过滤器
        
        Args:
            filter_func: 过滤器函数
        """
        for handler in logging.getLogger().handlers:
            handler.addFilter(filter_func)


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def init_logging(config: LogConfig) -> LogManager:
    """初始化日志系统
    
    Args:
        config: 日志配置
        
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager
    
    if _log_manager is None:
        _log_manager = LogManager(config)
        _log_manager.initialize()
    
    return _log_manager


def get_logger(
    name: str, 
    extra_context: Optional[Dict[str, Any]] = None
) -> LoggerAdapter:
    """获取日志记录器
    
    Args:
        name: 记录器名称
        extra_context: 额外上下文信息
        
    Returns:
        LoggerAdapter: 日志适配器
    """
    if _log_manager is None:
        # 如果未初始化，使用默认配置
        from .config import LogConfig
        init_logging(LogConfig())
    
    return _log_manager.get_logger(name, extra_context)


def get_structlog_logger(name: str) -> structlog.BoundLogger:
    """获取structlog记录器
    
    Args:
        name: 记录器名称
        
    Returns:
        structlog.BoundLogger: structlog记录器
    """
    if _log_manager is None:
        from .config import LogConfig
        init_logging(LogConfig())
    
    return _log_manager.get_structlog_logger(name)