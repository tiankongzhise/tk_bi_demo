"""配置管理器"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from tk_base_utils import load_toml,get_target_file_path

from .date_utils import DateRangeProcessor
from ..logger import logger_wrapper

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            env_path: 环境变量文件路径
        """
        self.config_path = config_path or get_target_file_path("config.toml")
        self.env_path = env_path or get_target_file_path(".env")
        self.date_processor = DateRangeProcessor()
        
        # 加载环境变量
        if os.path.exists(self.env_path):
            load_dotenv(self.env_path)
        
        # 加载配置文件
        self._config = load_toml(self.config_path)
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        self._config = load_toml(self.config_path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def db_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get('db_config', {})
    
    @property
    def logger_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logger', {})
    
    @property
    def retry_config(self) -> Dict[str, Any]:
        """获取重试配置"""
        return self.get('retry', {})
    
    @property
    def baidu_oauth_config(self) -> Dict[str, Any]:
        """获取百度OAuth配置"""
        return self.get('oauth', {}).get('baidu', {})
    
    @property
    def report_config(self,channel:str|None = None,report_name:str|None = None) -> Dict[str, Any]:
        """获取报告配置"""
        if channel is None:
            return self.get('report_config', {})
        if report_name is None:
            return self.get(f'report_config.{channel}', {})
        return self.get(f'report_config.{channel}.{report_name}',{})
    
    @property
    def baidu_account_structure_config(self) -> Dict[str, Any]:
        """获取百度账户结构配置"""
        return self.get('baidu_account_structure', {})
    
    @logger_wrapper()
    def get_baidu_report_config(self, report_name: str) -> Dict[str, Any]:
        """获取百度报告配置
        
        Args:
            report_name: 报告名称
            
        Returns:
            处理后的报告配置
        """
        config = self.get(f'report_config.baidu.{report_name}',{})


        if not config:
            return {}
        
        # 处理日期范围
        config = config.copy()
        if 'date_range' in config:
            start_date, end_date = self.date_processor.process_date_range(config['date_range'])
            config['startDate'] = start_date
            config['endDate'] = end_date
            # 删除date_range，避免传递给API
            del config['date_range']
        
        # 处理时间后缀
        if 'timeUnit' in config and config['timeUnit'] == 'HOUR':
            if 'startDate' in config and 'endDate' in config:
                start_date, end_date = self.date_processor.add_time_suffix(
                    config['startDate'], config['endDate'], config['timeUnit']
                )
                config['startDate'] = start_date
                config['endDate'] = end_date
        
        return config
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config


_global_config_manager = None

def get_config_settings(config_manager:ConfigManager|None =None) -> ConfigManager:
    """获取配置管理器实例"""
    global _global_config_manager
    
    if config_manager is None:
        if _global_config_manager is None:
            _global_config_manager = ConfigManager()
        return _global_config_manager
    return config_manager

def reload_config() -> None:
    """重新加载配置文件"""
    global _global_config_manager
    if _global_config_manager:
        _global_config_manager.reload_config()
