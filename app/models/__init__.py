"""数据模型模块

包含数据库模型和Pydantic验证模型的定义。
"""

# 数据库模型
from .database import (
    Base,
    TimestampMixin,
    AdData,
    TaskLog,
    PlatformAuth,
    SystemMetrics,
    DataQuality,
    create_tables,
    drop_tables
)

# Pydantic模型
from .schemas import (
    # 枚举
    PlatformEnum,
    TaskStatusEnum,
    DataStatusEnum,
    
    # 基础模型
    BaseSchema,
    
    # 业务模型
    AdMetrics,
    AdReportModel,
    TaskConfig,
    TaskResult,
    SystemMetricsModel,
    HealthCheckResult,
    PlatformAuthModel,
    DataQualityReport,
    
    # API模型
    APIResponse,
    BatchRequest,
    BatchResponse
)

__all__ = [
    # 数据库模型
    "Base",
    "TimestampMixin",
    "AdData",
    "TaskLog",
    "PlatformAuth",
    "SystemMetrics",
    "DataQuality",
    "create_tables",
    "drop_tables",
    
    # 枚举
    "PlatformEnum",
    "TaskStatusEnum",
    "DataStatusEnum",
    
    # Pydantic模型
    "BaseSchema",
    "AdMetrics",
    "AdReportModel",
    "TaskConfig",
    "TaskResult",
    "SystemMetricsModel",
    "HealthCheckResult",
    "PlatformAuthModel",
    "DataQualityReport",
    "APIResponse",
    "BatchRequest",
    "BatchResponse",
]