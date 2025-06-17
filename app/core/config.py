"""配置管理模块

提供统一的配置管理功能，支持环境变量和配置文件。
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional
from pathlib import Path
import os
import toml


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
    
    class Config:
        env_prefix = "DATABASE__"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def __init__(self, **kwargs):
        # 加载TOML配置
        toml_config = self._load_toml_config()
        if toml_config and "database" in toml_config:
            for key, value in toml_config["database"].items():
                if key not in kwargs:
                    kwargs[key] = value
        super().__init__(**kwargs)
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    
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
    
    class Config:
        env_prefix = "HTTP__"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def __init__(self, **kwargs):
        # 加载TOML配置
        toml_config = self._load_toml_config()
        if toml_config and "http" in toml_config:
            for key, value in toml_config["http"].items():
                if key not in kwargs:
                    kwargs[key] = value
        super().__init__(**kwargs)
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    

class RedisConfig(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    db: int = Field(default=0, description="Redis数据库")
    
    class Config:
        env_prefix = "REDIS__"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def __init__(self, **kwargs):
        # 加载TOML配置
        toml_config = self._load_toml_config()
        if toml_config and "redis" in toml_config:
            for key, value in toml_config["redis"].items():
                if key not in kwargs:
                    kwargs[key] = value
        super().__init__(**kwargs)
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    
    @property
    def url(self) -> str:
        """构建Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class PlatformConfig(BaseSettings):
    """广告平台配置"""
    name: str = Field(..., description="平台名称")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    secret_key: Optional[str] = Field(default=None, description="密钥")
    base_url: str = Field(..., description="API基础URL")
    rate_limit: int = Field(default=100, description="速率限制(每分钟)")
    timeout: int = Field(default=30, description="请求超时时间")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def __init__(self, platform_name: str = None, **kwargs):
        # 加载TOML配置
        toml_config = self._load_toml_config()
        if toml_config and "platforms" in toml_config and platform_name and platform_name in toml_config["platforms"]:
            for key, value in toml_config["platforms"][platform_name].items():
                if key not in kwargs:
                    kwargs[key] = value
        super().__init__(**kwargs)
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    

class LogConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="json", description="日志格式")
    file_path: str = Field(default="./logs/app.log", description="日志文件路径")
    max_size: str = Field(default="100MB", description="日志文件最大大小")
    backup_count: int = Field(default=7, description="日志文件备份数量")
    
    class Config:
        env_prefix = "LOG__"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def __init__(self, **kwargs):
        # 加载TOML配置
        toml_config = self._load_toml_config()
        if toml_config and "log" in toml_config:
            for key, value in toml_config["log"].items():
                if key not in kwargs:
                    kwargs[key] = value
        super().__init__(**kwargs)
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    

class MonitorConfig(BaseSettings):
    """监控配置"""
    enable: bool = Field(default=True, description="是否启用监控")
    interval: int = Field(default=60, description="监控间隔(秒)")
    alert_threshold: int = Field(default=90, description="告警阈值")
    
    class Config:
        env_prefix = "MONITOR__"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def __init__(self, **kwargs):
        # 加载TOML配置
        toml_config = self._load_toml_config()
        if toml_config and "monitor" in toml_config:
            for key, value in toml_config["monitor"].items():
                if key not in kwargs:
                    kwargs[key] = value
        super().__init__(**kwargs)
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    

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
        extra = "allow"
        
    def __init__(self, **kwargs):
        # 首先加载TOML配置
        toml_config = self._load_toml_config()
        
        # 合并TOML配置到kwargs
        if toml_config:
            kwargs = self._merge_configs(toml_config, kwargs)
        super().__init__(**kwargs)
        self._load_platform_configs()
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """加载TOML配置文件"""
        config_file = Path("config.toml")
        if config_file.exists():
            try:
                return toml.load(config_file)
            except Exception as e:
                print(f"警告: 加载TOML配置文件失败: {e}")
        return {}
    
    def _merge_configs(self, toml_config: Dict[str, Any], env_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并TOML配置和环境变量配置"""
        merged = env_config.copy()
        
        # 合并应用配置
        if "app" in toml_config:
            app_config = toml_config["app"]
            merged.update({
                "app_debug": app_config.get("debug", merged.get("app_debug")),
                "app_log_level": app_config.get("log_level", merged.get("app_log_level")),
                "app_env": app_config.get("env", merged.get("app_env"))
            })
        
        # 合并子配置
        for section in ["database", "http", "redis", "log", "monitor"]:
            if section in toml_config:
                section_config = toml_config[section]
                # 将TOML配置转换为环境变量格式
                for key, value in section_config.items():
                    env_key = f"{section}__{key}"
                    if env_key not in merged:
                        merged[env_key] = value
        
        return merged
    
    def _load_platform_configs(self):
        """加载平台配置"""
        # 首先从TOML文件加载平台配置
        toml_config = self._load_toml_config()
        platform_names = ["baidu", "sogou", "qihoo360", "shenma", "bytedance", "tencent"]
        
        for platform_name in platform_names:
            platform_config = {}
            
            # 从TOML配置加载非机密信息
            if "platforms" in toml_config and platform_name in toml_config["platforms"]:
                platform_config.update(toml_config["platforms"][platform_name])
            
            # 从环境变量加载机密信息
            platform_env_prefix = f"PLATFORMS__{platform_name.upper()}__"
            for key, value in os.environ.items():
                if key.startswith(platform_env_prefix):
                    config_key = key[len(platform_env_prefix):].lower()
                    platform_config[config_key] = value
            
            if platform_config and "name" in platform_config:
                try:
                    self.platforms[platform_name] = PlatformConfig(platform_name=platform_name, **platform_config)
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