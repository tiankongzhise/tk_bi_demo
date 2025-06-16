"""数据库模型定义

定义系统中使用的所有数据库表模型。
"""

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    JSON,
    Date,
    DateTime,
    Text,
    Integer,
    Numeric,
    Boolean,
    Index,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Dict, Any, Optional

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类

    为模型添加创建时间和更新时间字段。
    """

    created_at = Column(
        DateTime, default=func.now(), nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class AdData(Base, TimestampMixin):
    """广告数据表

    存储从各个广告平台采集的广告数据。
    """

    __tablename__ = "ad_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    platform = Column(String(20), nullable=False, comment="平台名称")
    campaign_id = Column(String(50), nullable=False, comment="广告计划ID")
    campaign_name = Column(String(200), comment="广告计划名称")
    account_id = Column(String(50), comment="账户ID")
    account_name = Column(String(200), comment="账户名称")
    metrics = Column(JSON, nullable=False, comment="广告指标数据(JSON格式)")
    report_date = Column(Date, nullable=False, comment="报表日期")
    data_source = Column(String(50), default="api", comment="数据来源")
    raw_data = Column(JSON, comment="原始数据(JSON格式)")
    status = Column(String(20), default="active", comment="数据状态")

    # 索引定义
    __table_args__ = (
        Index("idx_platform_date", "platform", "report_date"),
        Index("idx_campaign_date", "campaign_id", "report_date"),
        Index("idx_account_date", "account_id", "report_date"),
        Index("idx_created_at", "created_at"),
        Index("idx_status", "status"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    def __repr__(self) -> str:
        return f"<AdData(id={self.id}, platform={self.platform}, campaign_id={self.campaign_id}, date={self.report_date})>"


class TaskLog(Base, TimestampMixin):
    """任务日志表

    记录数据采集任务的执行情况。
    """

    __tablename__ = "task_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    task_id = Column(String(50), nullable=False, comment="任务ID")
    task_name = Column(String(100), comment="任务名称")
    platform = Column(String(20), nullable=False, comment="平台名称")
    task_type = Column(String(20), nullable=False, comment="任务类型")
    status = Column(
        String(20),
        nullable=False,
        comment="任务状态: pending/running/success/failed/timeout",
    )
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    duration = Column(Integer, comment="执行时长(秒)")
    error_code = Column(Integer, comment="错误码")
    error_message = Column(Text, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    metrics = Column(JSON, comment="任务指标(JSON格式)")
    config = Column(JSON, comment="任务配置(JSON格式)")

    __table_args__ = (
        Index("idx_task_platform", "task_id", "platform"),
        Index("idx_status_time", "status", "start_time"),
        Index("idx_platform_status", "platform", "status"),
        Index("idx_task_type", "task_type"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    def __repr__(self) -> str:
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, platform={self.platform}, status={self.status})>"


class PlatformAuth(Base, TimestampMixin):
    """平台认证信息表

    存储各个广告平台的认证信息和令牌。
    """

    __tablename__ = "platform_auth"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    platform = Column(String(20), nullable=False, unique=True, comment="平台名称")
    access_token = Column(Text, comment="访问令牌")
    refresh_token = Column(Text, comment="刷新令牌")
    token_type = Column(String(20), default="Bearer", comment="令牌类型")
    expires_at = Column(DateTime, comment="令牌过期时间")
    scope = Column(String(200), comment="授权范围")
    auth_data = Column(JSON, comment="认证相关数据(JSON格式)")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_used_at = Column(DateTime, comment="最后使用时间")

    __table_args__ = (
        Index("idx_platform_active", "platform", "is_active"),
        Index("idx_expires_at", "expires_at"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    def __repr__(self) -> str:
        return f"<PlatformAuth(id={self.id}, platform={self.platform}, is_active={self.is_active})>"


class SystemMetrics(Base, TimestampMixin):
    """系统监控指标表

    记录系统运行的各项监控指标。
    """

    __tablename__ = "system_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    metric_time = Column(DateTime, nullable=False, comment="指标时间")
    metric_type = Column(String(50), nullable=False, comment="指标类型")
    metric_name = Column(String(100), nullable=False, comment="指标名称")
    metric_value = Column(Numeric(15, 4), comment="指标值")
    metric_unit = Column(String(20), comment="指标单位")
    tags = Column(JSON, comment="标签信息(JSON格式)")
    additional_data = Column(JSON, comment="附加数据(JSON格式)")

    __table_args__ = (
        Index("idx_metric_time_type", "metric_time", "metric_type"),
        Index("idx_metric_name", "metric_name"),
        Index("idx_metric_time", "metric_time"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    def __repr__(self) -> str:
        return f"<SystemMetrics(id={self.id}, type={self.metric_type}, name={self.metric_name}, value={self.metric_value})>"


class DataQuality(Base, TimestampMixin):
    """数据质量表

    记录数据质量检查结果。
    """

    __tablename__ = "data_quality"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    check_time = Column(DateTime, nullable=False, comment="检查时间")
    platform = Column(String(20), nullable=False, comment="平台名称")
    check_type = Column(String(50), nullable=False, comment="检查类型")
    check_result = Column(
        String(20), nullable=False, comment="检查结果: pass/warning/error"
    )
    total_records = Column(Integer, comment="总记录数")
    valid_records = Column(Integer, comment="有效记录数")
    invalid_records = Column(Integer, comment="无效记录数")
    error_details = Column(JSON, comment="错误详情(JSON格式)")
    quality_score = Column(Numeric(5, 2), comment="质量评分(0-100)")

    __table_args__ = (
        Index("idx_check_time_platform", "check_time", "platform"),
        Index("idx_check_result", "check_result"),
        Index("idx_platform_type", "platform", "check_type"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    def __repr__(self) -> str:
        return f"<DataQuality(id={self.id}, platform={self.platform}, result={self.check_result}, score={self.quality_score})>"


# 数据库表创建函数
async def create_tables(engine):
    """创建所有数据库表

    Args:
        engine: 数据库引擎
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 数据库表删除函数
async def drop_tables(engine):
    """删除所有数据库表

    Args:
        engine: 数据库引擎
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
