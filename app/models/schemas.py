"""Pydantic数据模型定义

定义用于数据验证、序列化和API交换的Pydantic模型。
"""

from pydantic import BaseModel, Field, validator, model_validator
from datetime import date, datetime
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal
from enum import Enum


class PlatformEnum(str, Enum):
    """支持的广告平台枚举"""
    BAIDU = "baidu"
    SOGOU = "sogou"
    QIHOO360 = "qihoo360"
    SHENMA = "shenma"
    BYTEDANCE = "bytedance"
    TENCENT = "tencent"


class TaskStatusEnum(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class DataStatusEnum(str, Enum):
    """数据状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    ARCHIVED = "archived"


class BaseSchema(BaseModel):
    """基础模型类
    
    提供通用的配置和方法。
    """
    
    class Config:
        # 允许使用枚举值
        use_enum_values = True
        # 验证赋值
        validate_assignment = True
        # 允许额外字段
        extra = "forbid"
        # JSON编码器
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class AdMetrics(BaseSchema):
    """广告指标数据模型"""
    impressions: int = Field(ge=0, description="曝光量")
    clicks: int = Field(ge=0, description="点击量")
    cost: Decimal = Field(ge=0, description="消费金额")
    conversions: int = Field(ge=0, default=0, description="转化量")
    conversion_value: Optional[Decimal] = Field(ge=0, default=None, description="转化价值")
    
    # 计算指标
    ctr: Optional[float] = Field(None, description="点击率")
    cpc: Optional[Decimal] = Field(None, description="平均点击成本")
    cpa: Optional[Decimal] = Field(None, description="平均转化成本")
    roas: Optional[float] = Field(None, description="广告支出回报率")
    
    @validator("cost", "conversion_value", "cpc", "cpa")
    def validate_decimal_precision(cls, v):
        """验证小数精度"""
        if v is not None:
            return round(float(v), 2)
        return v
    
    @model_validator(mode='before')
    @classmethod
    def calculate_metrics(cls, values):
        """计算派生指标"""
        impressions = values.get("impressions", 0)
        clicks = values.get("clicks", 0)
        cost = values.get("cost", 0)
        conversions = values.get("conversions", 0)
        conversion_value = values.get("conversion_value", 0)
        
        # 计算点击率
        if impressions > 0:
            values["ctr"] = round((clicks / impressions) * 100, 2)
        
        # 计算平均点击成本
        if clicks > 0 and cost > 0:
            values["cpc"] = round(float(cost) / clicks, 2)
        
        # 计算平均转化成本
        if conversions > 0 and cost > 0:
            values["cpa"] = round(float(cost) / conversions, 2)
        
        # 计算广告支出回报率
        if cost > 0 and conversion_value:
            values["roas"] = round(float(conversion_value) / float(cost), 2)
        
        return values


class AdReportModel(BaseSchema):
    """广告报表数据模型"""
    platform: PlatformEnum = Field(..., description="平台名称")
    campaign_id: str = Field(..., min_length=1, max_length=50, description="广告计划ID")
    campaign_name: Optional[str] = Field(None, max_length=200, description="广告计划名称")
    account_id: Optional[str] = Field(None, max_length=50, description="账户ID")
    account_name: Optional[str] = Field(None, max_length=200, description="账户名称")
    
    # 广告指标
    metrics: AdMetrics = Field(..., description="广告指标")
    
    # 时间信息
    report_date: date = Field(..., description="报表日期")
    
    # 元数据
    data_source: str = Field(default="api", description="数据来源")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始数据")
    
    @validator("report_date")
    def validate_report_date(cls, v):
        """验证报表日期"""
        if v > date.today():
            raise ValueError("报表日期不能超过今天")
        return v
    
    @validator("campaign_id", "account_id")
    def validate_ids(cls, v):
        """验证ID格式"""
        if v and not v.strip():
            raise ValueError("ID不能为空字符串")
        return v.strip() if v else v


class TaskConfig(BaseSchema):
    """任务配置模型"""
    platform: PlatformEnum = Field(..., description="平台名称")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    account_ids: Optional[List[str]] = Field(None, description="账户ID列表")
    campaign_ids: Optional[List[str]] = Field(None, description="广告计划ID列表")
    retry_times: int = Field(default=3, ge=0, le=10, description="重试次数")
    timeout: int = Field(default=30, ge=5, le=300, description="超时时间(秒)")
    batch_size: int = Field(default=100, ge=1, le=1000, description="批处理大小")
    
    @validator("end_date")
    def validate_date_range(cls, v, values):
        """验证日期范围"""
        start_date = values.get("start_date")
        if start_date and v < start_date:
            raise ValueError("结束日期不能早于开始日期")
        return v


class TaskResult(BaseSchema):
    """任务执行结果模型"""
    task_id: str = Field(..., description="任务ID")
    task_name: Optional[str] = Field(None, description="任务名称")
    platform: PlatformEnum = Field(..., description="平台名称")
    status: TaskStatusEnum = Field(..., description="任务状态")
    
    # 时间信息
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[int] = Field(None, ge=0, description="执行时长(秒)")
    
    # 统计信息
    total_records: int = Field(default=0, ge=0, description="总记录数")
    processed_records: int = Field(default=0, ge=0, description="已处理记录数")
    success_records: int = Field(default=0, ge=0, description="成功记录数")
    error_records: int = Field(default=0, ge=0, description="错误记录数")
    
    # 错误信息
    error_code: Optional[int] = Field(None, description="错误码")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(default=0, ge=0, description="重试次数")
    
    # 配置和指标
    config: Optional[TaskConfig] = Field(None, description="任务配置")
    metrics: Optional[Dict[str, Any]] = Field(None, description="任务指标")
    
    @model_validator(mode='before')
    @classmethod
    def calculate_duration(cls, values):
        """计算执行时长"""
        start_time = values.get("start_time")
        end_time = values.get("end_time")
        
        if start_time and end_time:
            duration = int((end_time - start_time).total_seconds())
            values["duration"] = duration
        
        return values


class SystemMetricsModel(BaseSchema):
    """系统监控指标模型"""
    timestamp: datetime = Field(..., description="时间戳")
    
    # 系统资源指标
    cpu_usage: float = Field(ge=0, le=100, description="CPU使用率(%)")
    memory_usage: float = Field(ge=0, le=100, description="内存使用率(%)")
    disk_usage: float = Field(ge=0, le=100, description="磁盘使用率(%)")
    
    # 数据库指标
    db_connections: int = Field(ge=0, description="数据库连接数")
    db_pool_size: int = Field(ge=0, description="连接池大小")
    db_response_time: float = Field(ge=0, description="数据库响应时间(ms)")
    
    # 应用指标
    active_tasks: int = Field(ge=0, description="活跃任务数")
    task_queue_size: int = Field(ge=0, description="任务队列大小")
    success_rate: float = Field(ge=0, le=100, description="成功率(%)")
    
    # 网络指标
    network_in: Optional[float] = Field(None, ge=0, description="网络入流量(MB/s)")
    network_out: Optional[float] = Field(None, ge=0, description="网络出流量(MB/s)")
    
    # 自定义指标
    custom_metrics: Optional[Dict[str, float]] = Field(None, description="自定义指标")


class HealthCheckResult(BaseSchema):
    """健康检查结果模型"""
    status: str = Field(..., description="整体状态")
    timestamp: datetime = Field(..., description="检查时间")
    
    # 各组件状态
    database: bool = Field(..., description="数据库状态")
    redis: Optional[bool] = Field(None, description="Redis状态")
    external_apis: Optional[Dict[str, bool]] = Field(None, description="外部API状态")
    
    # 详细信息
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    response_time: Optional[float] = Field(None, ge=0, description="响应时间(ms)")


class PlatformAuthModel(BaseSchema):
    """平台认证模型"""
    platform: PlatformEnum = Field(..., description="平台名称")
    access_token: str = Field(..., description="访问令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    scope: Optional[str] = Field(None, description="授权范围")
    
    @validator("access_token")
    def validate_access_token(cls, v):
        """验证访问令牌"""
        if not v or not v.strip():
            raise ValueError("访问令牌不能为空")
        return v.strip()


class DataQualityReport(BaseSchema):
    """数据质量报告模型"""
    platform: PlatformEnum = Field(..., description="平台名称")
    check_time: datetime = Field(..., description="检查时间")
    check_type: str = Field(..., description="检查类型")
    
    # 统计信息
    total_records: int = Field(ge=0, description="总记录数")
    valid_records: int = Field(ge=0, description="有效记录数")
    invalid_records: int = Field(ge=0, description="无效记录数")
    
    # 质量评分
    quality_score: float = Field(ge=0, le=100, description="质量评分(0-100)")
    
    # 错误详情
    error_details: Optional[List[Dict[str, Any]]] = Field(None, description="错误详情")
    
    # 建议
    recommendations: Optional[List[str]] = Field(None, description="改进建议")
    
    @model_validator(mode='before')
    @classmethod
    def validate_record_counts(cls, values):
        """验证记录数统计"""
        total = values.get("total_records", 0)
        valid = values.get("valid_records", 0)
        invalid = values.get("invalid_records", 0)
        
        if valid + invalid != total:
            raise ValueError("有效记录数和无效记录数之和必须等于总记录数")
        
        return values


class APIResponse(BaseSchema):
    """API响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    error_code: Optional[int] = Field(None, description="错误码")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    @classmethod
    def success_response(
        cls, 
        data: Any = None, 
        message: str = "操作成功"
    ) -> "APIResponse":
        """创建成功响应"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(
        cls, 
        message: str, 
        error_code: Optional[int] = None,
        data: Any = None
    ) -> "APIResponse":
        """创建错误响应"""
        return cls(
            success=False, 
            message=message, 
            error_code=error_code,
            data=data
        )


# 批量操作模型
class BatchRequest(BaseSchema):
    """批量请求模型"""
    items: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000, description="批量数据")
    batch_id: Optional[str] = Field(None, description="批次ID")
    options: Optional[Dict[str, Any]] = Field(None, description="批量选项")


class BatchResponse(BaseSchema):
    """批量响应模型"""
    batch_id: str = Field(..., description="批次ID")
    total_items: int = Field(..., ge=0, description="总项目数")
    success_items: int = Field(..., ge=0, description="成功项目数")
    failed_items: int = Field(..., ge=0, description="失败项目数")
    results: List[Dict[str, Any]] = Field(..., description="处理结果")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="错误列表")