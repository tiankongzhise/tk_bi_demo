"""百度广告平台适配器

实现百度搜索推广API的数据采集功能。
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import json
import hashlib
import hmac
import base64
from urllib.parse import urlencode, quote

from .base_adapter import (
    BasePlatformAdapter,
    AuthConfig,
    APIEndpoints,
    RateLimitConfig
)
from ..core import (
    get_logger,
    PlatformAPIException,
    AuthenticationException
)
from ..models import PlatformEnum
from ..services import HTTPClient

logger = get_logger(__name__)


class BaiduAdapter(BasePlatformAdapter):
    """百度广告平台适配器
    
    实现百度搜索推广API的接口调用。
    """
    
    def __init__(self, auth_config: AuthConfig, http_client: HTTPClient):
        # 百度API端点配置
        api_endpoints = APIEndpoints(
            base_url="https://api.baidu.com",
            auth_url="https://api.baidu.com/oauth/2.0/authorize",
            token_url="https://api.baidu.com/oauth/2.0/token",
            report_url="https://api.baidu.com/json/sms/service/ReportService",
            account_url="https://api.baidu.com/json/sms/service/AccountService",
            campaign_url="https://api.baidu.com/json/sms/service/CampaignService"
        )
        
        # 速率限制配置
        rate_limit_config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=2000,
            requests_per_day=20000,
            burst_limit=20
        )
        
        super().__init__(
            platform=PlatformEnum.BAIDU,
            auth_config=auth_config,
            api_endpoints=api_endpoints,
            rate_limit_config=rate_limit_config,
            http_client=http_client
        )
        
        # 百度特有配置
        self.api_version = "4"
        self.format = "json"
    
    async def _authenticate(self) -> bool:
        """执行百度OAuth2认证流程
        
        Returns:
            bool: 认证是否成功
        """
        try:
            # 使用授权码获取访问令牌
            token_data = {
                "grant_type": "authorization_code",
                "code": self.auth_config.client_secret,  # 这里应该是授权码
                "client_id": self.auth_config.client_id,
                "client_secret": self.auth_config.client_secret,
                "redirect_uri": self.auth_config.redirect_uri or "http://localhost"
            }
            
            response = await self.http_client.post(
                self.api_endpoints.token_url,
                data=token_data
            )
            
            if "access_token" in response:
                self.auth_config.access_token = response["access_token"]
                self.auth_config.refresh_token = response.get("refresh_token")
                
                # 设置过期时间
                expires_in = response.get("expires_in", 3600)
                self.auth_config.token_expires_at = (
                    datetime.now() + timedelta(seconds=expires_in)
                )
                
                logger.info("百度平台认证成功")
                return True
            
            logger.error(f"百度平台认证失败: {response}")
            return False
            
        except Exception as e:
            logger.error(f"百度平台认证异常: {e}")
            return False
    
    async def _refresh_token(self) -> bool:
        """刷新百度访问令牌
        
        Returns:
            bool: 刷新是否成功
        """
        if not self.auth_config.refresh_token:
            return False
        
        try:
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": self.auth_config.refresh_token,
                "client_id": self.auth_config.client_id,
                "client_secret": self.auth_config.client_secret
            }
            
            response = await self.http_client.post(
                self.api_endpoints.token_url,
                data=refresh_data
            )
            
            if "access_token" in response:
                self.auth_config.access_token = response["access_token"]
                
                # 更新过期时间
                expires_in = response.get("expires_in", 3600)
                self.auth_config.token_expires_at = (
                    datetime.now() + timedelta(seconds=expires_in)
                )
                
                # 更新refresh_token（如果返回了新的）
                if "refresh_token" in response:
                    self.auth_config.refresh_token = response["refresh_token"]
                
                logger.info("百度平台Token刷新成功")
                return True
            
            logger.error(f"百度平台Token刷新失败: {response}")
            return False
            
        except Exception as e:
            logger.error(f"百度平台Token刷新异常: {e}")
            return False
    
    async def _get_report_data(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
        campaign_ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取百度报表数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 报表数据列表
        """
        start_date, end_date = self._parse_date_range(start_date, end_date)
        
        all_data = []
        
        # 如果没有指定账户，先获取所有账户
        if not account_ids:
            accounts = await self._get_account_info()
            account_ids = [acc["userId"] for acc in accounts]
        
        # 分批处理账户
        for account_chunk in self._chunk_list(account_ids, 10):
            try:
                chunk_data = await self._fetch_report_chunk(
                    start_date, end_date, account_chunk, campaign_ids, **kwargs
                )
                all_data.extend(chunk_data)
                
                # 避免触发速率限制
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(
                    f"获取百度报表数据块失败: {e}",
                    extra={"account_chunk": account_chunk}
                )
                # 继续处理其他块
                continue
        
        logger.info(
            f"百度平台报表数据获取完成",
            extra={
                "total_records": len(all_data),
                "date_range": f"{start_date} to {end_date}"
            }
        )
        
        return all_data
    
    async def _fetch_report_chunk(
        self,
        start_date: date,
        end_date: date,
        account_ids: List[str],
        campaign_ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取报表数据块
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 报表数据列表
        """
        # 构建报表请求参数
        report_request = {
            "reportRequestType": {
                "performanceData": [
                    "impression", "click", "cost", "ctr", "cpc", "cpm",
                    "conversion", "conversionRate", "conversionCost"
                ],
                "dimensionData": [
                    "accountId", "campaignId", "campaignName", 
                    "adgroupId", "adgroupName", "keywordId", "keyword",
                    "matchType", "device", "date"
                ]
            },
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "levelOfDetails": "KEYWORD",
            "reportType": "KEYWORD_REPORT",
            "statIds": account_ids
        }
        
        # 如果指定了广告计划，添加过滤条件
        if campaign_ids:
            report_request["idOnly"] = campaign_ids
        
        # 构建API请求
        api_request = {
            "header": {
                "token": self.auth_config.access_token,
                "username": account_ids[0] if account_ids else "",
                "password": "",
                "action": "getProfessionalReportId"
            },
            "body": report_request
        }
        
        try:
            # 提交报表请求
            response = await self.http_client.post(
                self.api_endpoints.report_url,
                json_data=api_request,
                headers=self._build_auth_headers()
            )
            
            if not self._is_success_response(response):
                raise PlatformAPIException(
                    f"百度报表请求失败: {response}",
                    platform=self.platform_name,
                    error_code=1004
                )
            
            report_id = response["body"]["data"]
            
            # 等待报表生成完成
            report_data = await self._wait_for_report(report_id)
            
            return report_data
            
        except Exception as e:
            logger.error(f"获取百度报表数据块异常: {e}")
            raise
    
    async def _wait_for_report(self, report_id: str, max_wait: int = 300) -> List[Dict[str, Any]]:
        """等待报表生成完成并获取数据
        
        Args:
            report_id: 报表ID
            max_wait: 最大等待时间（秒）
            
        Returns:
            List[Dict[str, Any]]: 报表数据
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait:
            # 检查报表状态
            status_request = {
                "header": {
                    "token": self.auth_config.access_token,
                    "username": "",
                    "password": "",
                    "action": "getReportState"
                },
                "body": {
                    "reportId": report_id
                }
            }
            
            status_response = await self.http_client.post(
                self.api_endpoints.report_url,
                json_data=status_request,
                headers=self._build_auth_headers()
            )
            
            if self._is_success_response(status_response):
                state = status_response["body"]["data"]
                
                if state == 3:  # 报表生成完成
                    # 获取报表数据
                    return await self._download_report(report_id)
                elif state == 4:  # 报表生成失败
                    raise PlatformAPIException(
                        f"百度报表生成失败: {report_id}",
                        platform=self.platform_name,
                        error_code=1004
                    )
            
            # 等待5秒后重试
            await asyncio.sleep(5)
        
        raise PlatformAPIException(
            f"百度报表生成超时: {report_id}",
            platform=self.platform_name,
            error_code=1001
        )
    
    async def _download_report(self, report_id: str) -> List[Dict[str, Any]]:
        """下载报表数据
        
        Args:
            report_id: 报表ID
            
        Returns:
            List[Dict[str, Any]]: 报表数据
        """
        download_request = {
            "header": {
                "token": self.auth_config.access_token,
                "username": "",
                "password": "",
                "action": "getReportFileUrl"
            },
            "body": {
                "reportId": report_id
            }
        }
        
        response = await self.http_client.post(
            self.api_endpoints.report_url,
            json_data=download_request,
            headers=self._build_auth_headers()
        )
        
        if not self._is_success_response(response):
            raise PlatformAPIException(
                f"获取百度报表下载链接失败: {response}",
                platform=self.platform_name,
                error_code=1004
            )
        
        file_url = response["body"]["data"]
        
        # 下载报表文件
        file_response = await self.http_client.get(file_url)
        
        # 解析CSV数据
        return self._parse_csv_data(file_response.get("content", ""))
    
    def _parse_csv_data(self, csv_content: str) -> List[Dict[str, Any]]:
        """解析CSV报表数据
        
        Args:
            csv_content: CSV内容
            
        Returns:
            List[Dict[str, Any]]: 解析后的数据
        """
        import csv
        import io
        
        data = []
        
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row in csv_reader:
                # 跳过空行和汇总行
                if not row or "汇总" in str(row):
                    continue
                
                data.append(row)
            
        except Exception as e:
            logger.error(f"解析百度CSV数据失败: {e}")
        
        return data
    
    async def _get_account_info(self, account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取百度账户信息
        
        Args:
            account_ids: 账户ID列表
            
        Returns:
            List[Dict[str, Any]]: 账户信息列表
        """
        request_data = {
            "header": {
                "token": self.auth_config.access_token,
                "username": "",
                "password": "",
                "action": "getAccountInfo"
            },
            "body": {}
        }
        
        if account_ids:
            request_data["body"]["userIds"] = account_ids
        
        response = await self.http_client.post(
            self.api_endpoints.account_url,
            json_data=request_data,
            headers=self._build_auth_headers()
        )
        
        if self._is_success_response(response):
            return response["body"]["data"]
        
        raise PlatformAPIException(
            f"获取百度账户信息失败: {response}",
            platform=self.platform_name,
            error_code=1004
        )
    
    async def _get_campaign_info(
        self, 
        account_ids: Optional[List[str]] = None,
        campaign_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取百度广告计划信息
        
        Args:
            account_ids: 账户ID列表
            campaign_ids: 广告计划ID列表
            
        Returns:
            List[Dict[str, Any]]: 广告计划信息列表
        """
        request_data = {
            "header": {
                "token": self.auth_config.access_token,
                "username": account_ids[0] if account_ids else "",
                "password": "",
                "action": "getCampaign"
            },
            "body": {}
        }
        
        if campaign_ids:
            request_data["body"]["campaignIds"] = campaign_ids
        
        response = await self.http_client.post(
            self.api_endpoints.campaign_url,
            json_data=request_data,
            headers=self._build_auth_headers()
        )
        
        if self._is_success_response(response):
            return response["body"]["data"]
        
        raise PlatformAPIException(
            f"获取百度广告计划信息失败: {response}",
            platform=self.platform_name,
            error_code=1004
        )
    
    async def _standardize_data(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """标准化百度数据格式
        
        Args:
            raw_record: 原始数据记录
            
        Returns:
            Dict[str, Any]: 标准化后的数据记录
        """
        # 百度字段映射
        field_mapping = {
            "accountId": "account_id",
            "campaignId": "campaign_id",
            "campaignName": "campaign_name",
            "adgroupId": "adgroup_id",
            "adgroupName": "adgroup_name",
            "keywordId": "keyword_id",
            "keyword": "keyword",
            "matchType": "match_type",
            "device": "device_type",
            "date": "report_date",
            "impression": "impressions",
            "click": "clicks",
            "cost": "cost",
            "ctr": "ctr",
            "cpc": "cpc",
            "cpm": "cpm",
            "conversion": "conversions",
            "conversionRate": "cvr",
            "conversionCost": "conversion_value"
        }
        
        standardized = {
            "platform": self.platform_name
        }
        
        # 映射字段
        for baidu_field, standard_field in field_mapping.items():
            if baidu_field in raw_record:
                value = raw_record[baidu_field]
                
                # 数据类型转换
                if standard_field in ["impressions", "clicks", "conversions"]:
                    standardized[standard_field] = int(float(value or 0))
                elif standard_field in ["cost", "ctr", "cpc", "cpm", "cvr", "conversion_value"]:
                    standardized[standard_field] = float(value or 0)
                elif standard_field == "report_date":
                    # 日期格式转换
                    if isinstance(value, str):
                        try:
                            standardized[standard_field] = datetime.strptime(value, "%Y-%m-%d").date()
                        except ValueError:
                            standardized[standard_field] = datetime.strptime(value, "%Y/%m/%d").date()
                    else:
                        standardized[standard_field] = value
                else:
                    standardized[standard_field] = str(value) if value is not None else None
        
        # 计算派生指标
        if "cost" in standardized and "conversions" in standardized:
            if standardized["conversions"] > 0:
                standardized["roas"] = standardized.get("conversion_value", 0) / standardized["cost"]
            else:
                standardized["roas"] = 0.0
        
        return standardized
    
    async def _check_api_connectivity(self) -> bool:
        """检查百度API连通性
        
        Returns:
            bool: API是否可连通
        """
        try:
            # 简单的账户信息查询来测试连通性
            request_data = {
                "header": {
                    "token": self.auth_config.access_token,
                    "username": "",
                    "password": "",
                    "action": "getAccountInfo"
                },
                "body": {}
            }
            
            response = await self.http_client.post(
                self.api_endpoints.account_url,
                json_data=request_data,
                headers=self._build_auth_headers(),
                timeout=10
            )
            
            return self._is_success_response(response)
            
        except Exception as e:
            logger.error(f"百度API连通性检查失败: {e}")
            return False
    
    def _is_success_response(self, response: Dict[str, Any]) -> bool:
        """检查响应是否成功
        
        Args:
            response: API响应
            
        Returns:
            bool: 是否成功
        """
        if not isinstance(response, dict):
            return False
        
        # 检查header中的状态
        header = response.get("header", {})
        if isinstance(header, dict):
            status = header.get("status", 0)
            return status == 0
        
        # 检查是否有错误信息
        return "error" not in response and "body" in response


def create_baidu_adapter(
    client_id: str,
    client_secret: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    http_client: Optional[HTTPClient] = None
) -> BaiduAdapter:
    """创建百度平台适配器
    
    Args:
        client_id: 客户端ID
        client_secret: 客户端密钥
        access_token: 访问令牌
        refresh_token: 刷新令牌
        http_client: HTTP客户端
        
    Returns:
        BaiduAdapter: 百度平台适配器实例
    """
    auth_config = AuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        refresh_token=refresh_token
    )
    
    if http_client is None:
        from ..services import get_http_manager
        from ..core import HTTPConfig
        
        http_manager = get_http_manager()
        http_client = http_manager.create_client(
            "baidu",
            HTTPConfig(),
            rate_limit=100
        )
    
    return BaiduAdapter(auth_config, http_client)