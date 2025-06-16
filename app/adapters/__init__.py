"""平台适配器模块

提供各广告平台的API适配器实现。
"""

from .base_adapter import (
    BasePlatformAdapter,
    AuthConfig,
    APIEndpoints,
    RateLimitConfig
)

from .baidu_adapter import (
    BaiduAdapter,
    create_baidu_adapter
)

# 平台适配器工厂
PLATFORM_ADAPTERS = {
    "baidu": BaiduAdapter,
    # 其他平台适配器将在后续添加
    # "sogou": SogouAdapter,
    # "qihoo360": Qihoo360Adapter,
    # "shenma": ShenmaAdapter,
    # "bytedance": BytedanceAdapter,
    # "tencent": TencentAdapter
}

PLATFORM_FACTORIES = {
    "baidu": create_baidu_adapter,
    # 其他平台工厂函数将在后续添加
}

__all__ = [
    # 基类
    "BasePlatformAdapter",
    "AuthConfig",
    "APIEndpoints",
    "RateLimitConfig",
    
    # 百度适配器
    "BaiduAdapter",
    "create_baidu_adapter",
    
    # 工厂
    "PLATFORM_ADAPTERS",
    "PLATFORM_FACTORIES"
]