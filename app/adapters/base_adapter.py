"""平台适配器基类

定义广告平台适配器的统一接口和基础功能。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from ..core import (
    get_logger,
    PlatformAPIException,
    AuthenticationException,
    RateLimitException
)
from ..models import (
    PlatformEnum,
    AdReportModel,
    PlatformAuthModel
)
from ..services import HTTPClient, RateLimiter

logger = get_logger(__name__)


@dataclass
class AuthConfig:
    """认证配置"""
    client_id: str
    client_secret: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    redirect_uri: Optional[str] = None


@dataclass
class APIEndpoints:
    """API端点配置"""
    base_url: str
    auth_url: str
    token_url: str
    report_url: str
    account_url: Optional[str] = None
    campaign_url: Optional[str] = None


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10


class BasePlatformAdapter(ABC):
    """平台适配器基类
    
    定义所有广告平台适配器必须实现的接口。
    """
    
    def __init__(
        self,
        platform: PlatformEnum,
        auth_config: AuthConfig,
        api_endpoints: APIEndpoints,
        rate_limit_config: RateLimitConfig,
        http_client: HTTPClient
    ):
        self.platform = platform
        self.auth_config = auth_config
        self.api_endpoints = api_endpoints
        self.rate_limit_config = rate_limit_config
        self.http_client = http_client
        
        # 速率限制器
        self.rate_limiter = RateLimiter(
            rate=rate_limit_config.requests_per_minute,
            per=60
        )
        
        # 认证状态
        self._authenticated = False
        self._auth_lock = asyncio.Lock()
        
        logger.info(
            f"{platform.value}平台适配器已初始化",
            extra={"platform": platform.value}
        )
    
    @property
    def platform_name(self) -> str:
        """平台名称"""
        return self.platform.value
    
    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return (
            self._authenticated and 
            self.auth_config.access_token and
            (
                not self.auth_config.token_expires_at or 
                self.auth_config.token_expires_at > datetime.now()
            )
        )
    
    async def authenticate(self) -> bool:
        """认证
        
        Returns:
            bool: 认证是否成功
        """
        async with self._auth_lock:
            if self.is_authenticated:
                return True
            
            try:
                logger.info(f"开始{self.platform_name}平台认证")
                
                # 如果有refresh_token，尝试刷新
                if self.auth_config.refresh_token:
                    success = await self._refresh_token()
                    if success:
                        self._authenticated = True
                        logger.info(f"{self.platform_name}平台Token刷新成功")
                        return True
                
                # 否则进行完整认证流程
                success = await self._authenticate()
                if success:
                    self._authenticated = True
                    logger.info(f"{self.platform_name}平台认证成功")
                    return True
                
                logger.error(f"{self.platform_name}平台认证失败")
                return False
                
            except Exception as e:
                logger.error(
                    f"{self.platform_name}平台认证异常: {e}",
                    extra={"error": str(e)}
                )
                raise AuthenticationException(
                    f"{self.platform_name}平台认证失败: {e}",
                    platform=self.platform_name,
                    error_code=1002
                )
    
    async def get_report_data(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
        campaign_ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取报表数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 报表数据列表
            
        Raises:
            PlatformAPIException: API调用异常
            AuthenticationException: 认证异常
        """
        # 确保已认证
        if not await self.authenticate():
            raise AuthenticationException(
                f"{self.platform_name}平台认证失败",
                platform=self.platform_name,
                error_code=1002
            )
        
        # 速率限制
        await self.rate_limiter.wait_for_token()
        
        try:
            logger.info(
                f"开始获取{self.platform_name}平台报表数据",
                extra={
                    "platform": self.platform_name,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "account_count": len(account_ids) if account_ids else 0,
                    "campaign_count": len(campaign_ids) if campaign_ids else 0
                }
            )
            
            # 调用具体平台的实现
            data = await self._get_report_data(
                start_date, end_date, account_ids, campaign_ids, **kwargs
            )
            
            logger.info(
                f"{self.platform_name}平台报表数据获取完成",
                extra={
                    "platform": self.platform_name,
                    "record_count": len(data)
                }
            )
            
            return data
            
        except Exception as e:
            logger.error(
                f"{self.platform_name}平台报表数据获取失败: {e}",
                extra={"error": str(e)}
            )
            
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                # 认证失效，清除认证状态
                self._authenticated = False
                raise AuthenticationException(
                    f"{self.platform_name}平台认证失效: {e}",
                    platform=self.platform_name,
                    error_code=1002
                )
            
            raise PlatformAPIException(
                f"{self.platform_name}平台API调用失败: {e}",
                platform=self.platform_name,
                error_code=1004
            )
    
    async def get_account_info(self, account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取账户信息
        
        Args:
            account_ids: 账户ID列表
            
        Returns:
            List[Dict[str, Any]]: 账户信息列表
        """
        if not await self.authenticate():
            raise AuthenticationException(
                f"{self.platform_name}平台认证失败",
                platform=self.platform_name,
                error_code=1002
            )
        
        await self.rate_limiter.wait_for_token()
        
        try:
            return await self._get_account_info(account_ids)
        except Exception as e:
            logger.error(f"{self.platform_name}平台获取账户信息失败: {e}")
            raise PlatformAPIException(
                f"{self.platform_name}平台获取账户信息失败: {e}",
                platform=self.platform_name,
                error_code=1004
            )
    
    async def get_campaign_info(
        self, 
        account_ids: Optional[List[str]] = None,
        campaign_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取广告计划信息
        
        Args:
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            
        Returns:
            List[Dict[str, Any]]: 广告计划信息列表
        """
        if not await self.authenticate():
            raise AuthenticationException(
                f"{self.platform_name}平台认证失败",
                platform=self.platform_name,
                error_code=1002
            )
        
        await self.rate_limiter.wait_for_token()
        
        try:
            return await self._get_campaign_info(account_ids, campaign_ids)
        except Exception as e:
            logger.error(f"{self.platform_name}平台获取广告计划信息失败: {e}")
            raise PlatformAPIException(
                f"{self.platform_name}平台获取广告计划信息失败: {e}",
                platform=self.platform_name,
                error_code=1004
            )
    
    async def validate_data(self, raw_data: List[Dict[str, Any]]) -> List[AdReportModel]:
        """验证和转换数据
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            List[AdReportModel]: 验证后的数据列表
        """
        validated_data = []
        
        for i, record in enumerate(raw_data):
            try:
                # 转换为标准格式
                standardized = await self._standardize_data(record)
                
                # 使用Pydantic验证
                validated = AdReportModel(**standardized)
                validated_data.append(validated)
                
            except Exception as e:
                logger.warning(
                    f"{self.platform_name}平台数据验证失败",
                    extra={
                        "record_index": i,
                        "error": str(e),
                        "raw_data": record
                    }
                )
        
        logger.info(
            f"{self.platform_name}平台数据验证完成",
            extra={
                "total_records": len(raw_data),
                "valid_records": len(validated_data),
                "invalid_records": len(raw_data) - len(validated_data)
            }
        )
        
        return validated_data
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            start_time = datetime.now()
            
            # 检查认证状态
            auth_status = await self.authenticate()
            
            # 检查API连通性
            api_status = await self._check_api_connectivity()
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "platform": self.platform_name,
                "status": "healthy" if auth_status and api_status else "unhealthy",
                "authentication": "success" if auth_status else "failed",
                "api_connectivity": "success" if api_status else "failed",
                "response_time": response_time,
                "timestamp": datetime.now().isoformat(),
                "token_expires_at": (
                    self.auth_config.token_expires_at.isoformat() 
                    if self.auth_config.token_expires_at else None
                )
            }
            
        except Exception as e:
            logger.error(f"{self.platform_name}平台健康检查失败: {e}")
            return {
                "platform": self.platform_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # 抽象方法 - 子类必须实现
    
    @abstractmethod
    async def _authenticate(self) -> bool:
        """执行认证流程
        
        Returns:
            bool: 认证是否成功
        """
        pass
    
    @abstractmethod
    async def _refresh_token(self) -> bool:
        """刷新访问令牌
        
        Returns:
            bool: 刷新是否成功
        """
        pass
    
    @abstractmethod
    async def _get_report_data(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
        campaign_ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取报表数据的具体实现
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 报表数据列表
        """
        pass
    
    @abstractmethod
    async def _get_account_info(self, account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取账户信息的具体实现
        
        Args:
            account_ids: 账户ID列表
            
        Returns:
            List[Dict[str, Any]]: 账户信息列表
        """
        pass
    
    @abstractmethod
    async def _get_campaign_info(
        self, 
        account_ids: Optional[List[str]] = None,
        campaign_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取广告计划信息的具体实现
        
        Args:
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            
        Returns:
            List[Dict[str, Any]]: 广告计划信息列表
        """
        pass
    
    @abstractmethod
    async def _standardize_data(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """标准化数据格式
        
        Args:
            raw_record: 原始数据记录
            
        Returns:
            Dict[str, Any]: 标准化后的数据记录
        """
        pass
    
    @abstractmethod
    async def _check_api_connectivity(self) -> bool:
        """检查API连通性
        
        Returns:
            bool: API是否可连通
        """
        pass
    
    # 辅助方法
    
    def _build_auth_headers(self) -> Dict[str, str]:
        """构建认证请求头
        
        Returns:
            Dict[str, str]: 请求头字典
        """
        if not self.auth_config.access_token:
            return {}
        
        return {
            "Authorization": f"Bearer {self.auth_config.access_token}",
            "Content-Type": "application/json"
        }
    
    def _parse_date_range(self, start_date: date, end_date: date) -> Tuple[date, date]:
        """解析和验证日期范围
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Tuple[date, date]: 验证后的日期范围
            
        Raises:
            ValueError: 日期范围无效
        """
        if start_date > end_date:
            raise ValueError("开始日期不能大于结束日期")
        
        # 限制查询范围（最多90天）
        max_days = 90
        if (end_date - start_date).days > max_days:
            raise ValueError(f"查询范围不能超过{max_days}天")
        
        # 不能查询未来日期
        today = date.today()
        if start_date > today:
            raise ValueError("不能查询未来日期")
        
        if end_date > today:
            end_date = today
        
        return start_date, end_date
    
    def _chunk_list(self, items: List[Any], chunk_size: int) -> List[List[Any]]:
        """将列表分块
        
        Args:
            items: 原始列表
            chunk_size: 块大小
            
        Returns:
            List[List[Any]]: 分块后的列表
        """
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    async def _handle_rate_limit(self, retry_after: Optional[int] = None) -> None:
        """处理速率限制
        
        Args:
            retry_after: 重试等待时间（秒）
        """
        wait_time = retry_after or 60
        
        logger.warning(
            f"{self.platform_name}平台触发速率限制，等待{wait_time}秒",
            extra={"wait_time": wait_time}
        )
        
        await asyncio.sleep(wait_time)
    
    def get_auth_model(self) -> PlatformAuthModel:
        """获取认证信息模型
        
        Returns:
            PlatformAuthModel: 认证信息模型
        """
        return PlatformAuthModel(
            platform=self.platform,
            client_id=self.auth_config.client_id,
            access_token=self.auth_config.access_token,
            refresh_token=self.auth_config.refresh_token,
            token_expires_at=self.auth_config.token_expires_at,
            scope=self.auth_config.scope
        )