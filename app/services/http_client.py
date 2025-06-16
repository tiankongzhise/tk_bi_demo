"""HTTP客户端服务模块

提供异步HTTP请求管理、连接池和错误处理功能。
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin, urlencode
from datetime import datetime, timedelta

from ..core import (
    HTTPConfig, 
    get_logger, 
    HTTPClientException,
    RateLimitException
)
from ..utils.retry import retry_async

logger = get_logger(__name__)


class RateLimiter:
    """速率限制器
    
    实现令牌桶算法进行速率控制。
    """
    
    def __init__(self, rate: int, per: int = 60):
        """
        Args:
            rate: 速率限制（请求数）
            per: 时间窗口（秒）
        """
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_update = datetime.now()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """获取令牌
        
        Returns:
            bool: 是否成功获取令牌
        """
        async with self._lock:
            now = datetime.now()
            time_passed = (now - self.last_update).total_seconds()
            
            # 补充令牌
            self.tokens = min(
                self.rate, 
                self.tokens + time_passed * (self.rate / self.per)
            )
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    async def wait_for_token(self) -> None:
        """等待获取令牌"""
        while not await self.acquire():
            await asyncio.sleep(0.1)

    def __eq__(self, other: "RateLimiter") -> bool:
        """比较速率限制器是否相等
        
        Args:
            other: 另一个速率限制器
        
        Returns:
            bool: 是否相等
        """
        return self.rate == other.rate and self.per == other.per

class HTTPClient:
    """HTTP客户端
    
    提供异步HTTP请求功能，支持连接池、重试、速率限制等特性。
    """
    
    def __init__(self, config: HTTPConfig, rate_limiter: Optional[RateLimiter] = None):
        self.config = config
        self.rate_limiter = rate_limiter
        self.session: Optional[aiohttp.ClientSession] = None
        self._closed = False
    
    async def __aenter__(self) -> "HTTPClient":
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()
    
    async def start(self) -> None:
        """启动HTTP客户端"""
        if self.session is not None:
            return
        
        # 配置连接器
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # 配置超时
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_read=self.config.timeout
        )
        
        # 创建会话
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "AdDataCollector/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            },
            json_serialize=json.dumps,
            raise_for_status=False
        )
        
        self._closed = False
        logger.info("HTTP客户端已启动")
    
    async def close(self) -> None:
        """关闭HTTP客户端"""
        if self.session and not self._closed:
            await self.session.close()
            self._closed = True
            logger.info("HTTP客户端已关闭")
    
    def _ensure_session(self) -> None:
        """确保会话已创建"""
        if self.session is None or self._closed:
            raise HTTPClientException(
                "HTTP客户端未启动或已关闭",
                url="",
                error_code=4004
            )
    
    @retry_async(
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
    )
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        timeout: Optional[int] = None,
        allow_redirects: bool = True
    ) -> Dict[str, Any]:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: URL参数
            json_data: JSON数据
            data: 请求体数据
            timeout: 超时时间
            allow_redirects: 是否允许重定向
            
        Returns:
            Dict[str, Any]: 响应数据
            
        Raises:
            HTTPClientException: HTTP请求异常
            RateLimitException: 速率限制异常
        """
        self._ensure_session()
        
        # 速率限制
        if self.rate_limiter:
            if not await self.rate_limiter.acquire():
                raise RateLimitException(
                    "请求速率超过限制",
                    platform="http_client",
                    error_code=1003
                )
        
        # 准备请求参数
        request_kwargs = {
            "headers": headers,
            "params": params,
            "allow_redirects": allow_redirects
        }
        
        if json_data is not None:
            request_kwargs["json"] = json_data
        elif data is not None:
            request_kwargs["data"] = data
        
        if timeout:
            request_kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
        
        start_time = datetime.now()
        
        try:
            logger.debug(
                "发送HTTP请求",
                extra={
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "params": params
                }
            )
            
            async with self.session.request(method, url, **request_kwargs) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                
                # 记录响应信息
                logger.debug(
                    "收到HTTP响应",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status,
                        "response_time": response_time,
                        "content_type": response.content_type
                    }
                )
                
                # 处理响应状态码
                if response.status >= 400:
                    error_text = await response.text()
                    
                    if response.status == 429:
                        # 速率限制
                        retry_after = response.headers.get("Retry-After")
                        raise RateLimitException(
                            f"API速率限制: {error_text}",
                            platform="http_client",
                            retry_after=int(retry_after) if retry_after else None,
                            error_code=1003
                        )
                    
                    raise HTTPClientException(
                        f"HTTP请求失败: {response.status} {error_text}",
                        url=url,
                        method=method,
                        status_code=response.status,
                        error_code=1001 if response.status >= 500 else 1004
                    )
                
                # 解析响应内容
                if response.content_type == "application/json":
                    return await response.json()
                else:
                    text_content = await response.text()
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return {"content": text_content}
        
        except aiohttp.ClientError as e:
            logger.error(
                "HTTP客户端错误",
                extra={
                    "method": method,
                    "url": url,
                    "error": str(e)
                }
            )
            raise HTTPClientException(
                f"HTTP客户端错误: {e}",
                url=url,
                method=method,
                error_code=4004
            )
        
        except asyncio.TimeoutError:
            logger.error(
                "HTTP请求超时",
                extra={
                    "method": method,
                    "url": url,
                    "timeout": timeout or self.config.timeout
                }
            )
            raise HTTPClientException(
                "HTTP请求超时",
                url=url,
                method=method,
                error_code=1001
            )
    
    async def get(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送GET请求"""
        return await self.request("GET", url, params=params, headers=headers, **kwargs)
    
    async def post(
        self, 
        url: str, 
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送POST请求"""
        return await self.request(
            "POST", url, json_data=json_data, data=data, headers=headers, **kwargs
        )
    
    async def put(
        self, 
        url: str, 
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送PUT请求"""
        return await self.request(
            "PUT", url, json_data=json_data, data=data, headers=headers, **kwargs
        )
    
    async def delete(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送DELETE请求"""
        return await self.request("DELETE", url, headers=headers, **kwargs)
    
    async def download(
        self, 
        url: str, 
        file_path: str,
        headers: Optional[Dict[str, str]] = None,
        chunk_size: int = 8192
    ) -> None:
        """下载文件
        
        Args:
            url: 下载URL
            file_path: 保存路径
            headers: 请求头
            chunk_size: 块大小
        """
        self._ensure_session()
        
        try:
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                
                with open(file_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
                
                logger.info(f"文件下载完成: {file_path}")
        
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            raise HTTPClientException(
                f"文件下载失败: {e}",
                url=url,
                method="GET",
                error_code=4003
            )
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息
        
        Returns:
            Dict[str, Any]: 连接信息
        """
        if not self.session or self._closed:
            return {"status": "closed"}
        
        connector = self.session.connector
        return {
            "status": "active",
            "total_connections": len(connector._conns),
            "available_connections": len(connector._available_connections(None)),
            "limit": connector.limit,
            "limit_per_host": connector.limit_per_host
        }


class HTTPClientManager:
    """HTTP客户端管理器
    
    管理多个HTTP客户端实例。
    """
    
    def __init__(self):
        self._clients: Dict[str, HTTPClient] = {}
    
    def create_client(
        self, 
        name: str, 
        config: HTTPConfig,
        rate_limit: Optional[int] = None
    ) -> HTTPClient:
        """创建HTTP客户端
        
        Args:
            name: 客户端名称
            config: HTTP配置
            rate_limit: 速率限制
            
        Returns:
            HTTPClient: HTTP客户端实例
        """
        rate_limiter = RateLimiter(rate_limit) if rate_limit else None
        client = HTTPClient(config, rate_limiter)
        self._clients[name] = client
        return client
    
    def get_client(self, name: str) -> Optional[HTTPClient]:
        """获取HTTP客户端
        
        Args:
            name: 客户端名称
            
        Returns:
            Optional[HTTPClient]: HTTP客户端实例
        """
        return self._clients.get(name)
    
    async def close_all(self) -> None:
        """关闭所有客户端"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        logger.info("所有HTTP客户端已关闭")


# 全局HTTP客户端管理器
_http_manager = HTTPClientManager()


def get_http_manager() -> HTTPClientManager:
    """获取HTTP客户端管理器
    
    Returns:
        HTTPClientManager: HTTP客户端管理器实例
    """
    return _http_manager
