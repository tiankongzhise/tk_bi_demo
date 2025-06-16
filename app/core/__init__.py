"""核心模块

提供应用的核心功能，包括配置管理、数据库连接、日志系统和异常处理。
"""

from .config import (
    AppConfig,
    DatabaseConfig,
    HTTPConfig,
    RedisConfig,
    PlatformConfig,
    LogConfig,
    MonitorConfig,
    get_config,
    reload_config
)

from .database import (
    DatabaseManager,
    init_database,
    get_database,
    close_database
)

from .logging import (
    LogManager,
    LoggerAdapter,
    init_logging,
    get_logger,
    get_structlog_logger
)

from .exceptions import (
    BaseAppException,
    ConfigurationException,
    DatabaseException,
    PlatformAPIException,
    AuthenticationException,
    RateLimitException,
    DataValidationException,
    HTTPClientException,
    TaskException,
    RetryExhaustedException,
    ERROR_CODES,
    get_error_message,
    create_exception_from_code
)

__all__ = [
    # 配置相关
    "AppConfig",
    "DatabaseConfig",
    "HTTPConfig",
    "RedisConfig",
    "PlatformConfig",
    "LogConfig",
    "MonitorConfig",
    "get_config",
    "reload_config",
    
    # 数据库相关
    "DatabaseManager",
    "init_database",
    "get_database",
    "close_database",
    
    # 日志相关
    "LogManager",
    "LoggerAdapter",
    "init_logging",
    "get_logger",
    "get_structlog_logger",
    
    # 异常相关
    "BaseAppException",
    "ConfigurationException",
    "DatabaseException",
    "PlatformAPIException",
    "AuthenticationException",
    "RateLimitException",
    "DataValidationException",
    "HTTPClientException",
    "TaskException",
    "RetryExhaustedException",
    "ERROR_CODES",
    "get_error_message",
    "create_exception_from_code",
]