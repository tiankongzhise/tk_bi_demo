"""配置管理模块

提供统一的配置管理功能，支持环境变量和配置文件。
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional
from pathlib import Path
import os


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=3306, description="数据库端口")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")
    database: str = Field(..., description="数据库名称")
    pool_size: int = Field(default=20, description="连接池大小")
    max_overflow: int = Field(default=10, description="连接池最大溢出")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    
    @property
    def url(self) -> str:
        """构建数据库连接URL"""
        return f"mysql+asyncmy://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class HTTPConfig(BaseSettings):
    """HTTP客户端配置"""
    timeout: int = Field(default=30, description="请求超时时间")
    max_connections: int = Field(default=100, description="最大连接数")
    retry_times: int = Field(default=3, description="重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟")
    

class RedisConfig(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    db: int = Field(default=0, description="Redis数据库")
    
    @property
    def url(self) -> str:
        """构建Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class PlatformConfig(BaseSettings):
    """广告平台配置"""
    name: str = Field(..., description="平台名称")
    api_key: str = Field(..., description="API密钥")
    secret_key: str = Field(..., description="密钥")
    base_url: str = Field(..., description="API基础URL")
    rate_limit: int = Field(default=100, description="速率限制(每分钟)")
    timeout: int = Field(default=30, description="请求超时时间")
    

class LogConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="json", description="日志格式")
    file_path: str = Field(default="./logs/app.log", description="日志文件路径")
    max_size: str = Field(default="100MB", description="日志文件最大大小")
    backup_count: int = Field(default=7, description="日志文件备份数量")
    

class MonitorConfig(BaseSettings):
    """监控配置"""
    enable: bool = Field(default=True, description="是否启用监控")
    interval: int = Field(default=60, description="监控间隔(秒)")
    alert_threshold: int = Field(default=90, description="告警阈值")
    

class AppConfig(BaseSettings):
    """应用主配置"""
    app_debug: bool = Field(default=False, description="调试模式")
    app_log_level: str = Field(default="INFO", description="日志级别")
    app_env: str = Field(default="development", description="运行环境")
    
    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    
    # 平台配置
    platforms: Dict[str, PlatformConfig] = Field(default_factory=dict)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_platform_configs()
    
    def _load_platform_configs(self):
        """加载平台配置"""
        platform_names = ["baidu", "sogou", "qihoo360", "shenma", "bytedance", "tencent"]
        
        for platform_name in platform_names:
            # 从环境变量加载平台配置
            platform_env_prefix = f"PLATFORMS__{platform_name.upper()}__"
            platform_config = {}
            
            for key, value in os.environ.items():
                if key.startswith(platform_env_prefix):
                    config_key = key[len(platform_env_prefix):].lower()
                    platform_config[config_key] = value
            
            if platform_config:
                try:
                    self.platforms[platform_name] = PlatformConfig(**platform_config)
                except Exception as e:
                    print(f"警告: 加载{platform_name}平台配置失败: {e}")
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.app_env.lower() == "development"


# 全局配置实例
config = AppConfig()


def get_config() -> AppConfig:
    """获取配置实例"""
    return config


def reload_config() -> AppConfig:
    """重新加载配置"""
    global config
    config = AppConfig()
    return config