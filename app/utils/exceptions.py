"""异常定义模块

定义系统中使用的各种异常类型和错误码。
"""

from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """应用基础异常类
    
    所有自定义异常的基类，提供统一的异常处理接口。
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationException(BaseAppException):
    """配置异常
    
    当配置文件缺失、格式错误或配置项无效时抛出。
    """
    pass


class DatabaseException(BaseAppException):
    """数据库异常
    
    数据库连接、操作失败时抛出。
    """
    pass


class PlatformAPIException(BaseAppException):
    """平台API异常
    
    调用广告平台API失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        platform: str,
        error_code: Optional[int] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.platform = platform
        self.status_code = status_code
        self.response_data = response_data or {}
        
        details = {
            "platform": platform,
            "status_code": status_code,
            "response_data": response_data
        }
        
        super().__init__(message, error_code, details)


class AuthenticationException(BaseAppException):
    """认证异常
    
    平台认证失败、令牌过期等情况时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        platform: str,
        error_code: Optional[int] = None
    ):
        self.platform = platform
        details = {"platform": platform}
        super().__init__(message, error_code, details)


class RateLimitException(BaseAppException):
    """速率限制异常
    
    API调用超过速率限制时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        platform: str,
        retry_after: Optional[int] = None,
        error_code: Optional[int] = None
    ):
        self.platform = platform
        self.retry_after = retry_after
        
        details = {
            "platform": platform,
            "retry_after": retry_after
        }
        
        super().__init__(message, error_code, details)


class DataValidationException(BaseAppException):
    """数据验证异常
    
    数据格式错误、字段缺失等验证失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        error_code: Optional[int] = None
    ):
        self.field = field
        self.value = value
        
        details = {
            "field": field,
            "value": str(value) if value is not None else None
        }
        
        super().__init__(message, error_code, details)


class HTTPClientException(BaseAppException):
    """HTTP客户端异常
    
    HTTP请求失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        url: str,
        method: str = "GET",
        status_code: Optional[int] = None,
        error_code: Optional[int] = None
    ):
        self.url = url
        self.method = method
        self.status_code = status_code
        
        details = {
            "url": url,
            "method": method,
            "status_code": status_code
        }
        
        super().__init__(message, error_code, details)


class TaskException(BaseAppException):
    """任务执行异常
    
    任务调度、执行失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        task_id: str,
        task_type: Optional[str] = None,
        error_code: Optional[int] = None
    ):
        self.task_id = task_id
        self.task_type = task_type
        
        details = {
            "task_id": task_id,
            "task_type": task_type
        }
        
        super().__init__(message, error_code, details)


class RetryExhaustedException(BaseAppException):
    """重试耗尽异常
    
    重试次数用完仍然失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        attempts: int,
        last_error: Optional[Exception] = None,
        error_code: Optional[int] = None
    ):
        self.attempts = attempts
        self.last_error = last_error
        
        details = {
            "attempts": attempts,
            "last_error": str(last_error) if last_error else None
        }
        
        super().__init__(message, error_code, details)


# 错误码定义
ERROR_CODES = {
    # 1000-1999: API相关错误
    1001: "API请求超时",
    1002: "认证失效",
    1003: "API限流",
    1004: "API响应格式错误",
    1005: "API服务不可用",
    
    # 2000-2999: 数据相关错误
    2001: "数据校验失败",
    2002: "数据格式错误",
    2003: "必填字段缺失",
    2004: "数据类型错误",
    2005: "数据范围超出限制",
    
    # 3000-3999: 数据库相关错误
    3001: "数据库连接异常",
    3002: "数据库操作失败",
    3003: "事务回滚",
    3004: "数据库超时",
    3005: "数据库约束违反",
    
    # 4000-4999: 系统相关错误
    4001: "配置错误",
    4002: "系统资源不足",
    4003: "文件操作失败",
    4004: "网络连接失败",
    4005: "服务不可用",
    
    # 5000-5999: 业务逻辑错误
    5001: "任务执行失败",
    5002: "重试次数耗尽",
    5003: "并发限制超出",
    5004: "任务状态异常",
    5005: "业务规则违反",
}


def get_error_message(error_code: int) -> str:
    """根据错误码获取错误信息
    
    Args:
        error_code: 错误码
        
    Returns:
        str: 错误信息
    """
    return ERROR_CODES.get(error_code, f"未知错误码: {error_code}")


def create_exception_from_code(
    error_code: int, 
    message: Optional[str] = None,
    **kwargs
) -> BaseAppException:
    """根据错误码创建异常
    
    Args:
        error_code: 错误码
        message: 自定义错误信息
        **kwargs: 其他参数
        
    Returns:
        BaseAppException: 异常实例
    """
    if message is None:
        message = get_error_message(error_code)
    
    # 根据错误码范围选择异常类型
    if 1000 <= error_code < 2000:
        return PlatformAPIException(message, error_code=error_code, **kwargs)
    elif 2000 <= error_code < 3000:
        return DataValidationException(message, error_code=error_code, **kwargs)
    elif 3000 <= error_code < 4000:
        return DatabaseException(message, error_code=error_code, **kwargs)
    elif 4000 <= error_code < 5000:
        return ConfigurationException(message, error_code=error_code, **kwargs)
    elif 5000 <= error_code < 6000:
        return TaskException(message, error_code=error_code, **kwargs)
    else:
        return BaseAppException(message, error_code=error_code, **kwargs)
