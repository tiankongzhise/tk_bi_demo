#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置读取功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import (
    DatabaseConfig, HTTPConfig, RedisConfig, 
    PlatformConfig, LogConfig, MonitorConfig, AppConfig
)

def test_database_config():
    """测试数据库配置"""
    print("=== 测试 DatabaseConfig ===")
    db_config = DatabaseConfig(username="test_user", password="test_pass")
    print(f"Host: {db_config.host}")
    print(f"Port: {db_config.port}")
    print(f"Database: {db_config.database}")
    print(f"Pool Size: {db_config.pool_size}")
    print()

def test_http_config():
    """测试HTTP配置"""
    print("=== 测试 HTTPConfig ===")
    http_config = HTTPConfig()
    print(f"Timeout: {http_config.timeout}")
    print(f"Max Connections: {http_config.max_connections}")
    print(f"Retry Times: {http_config.retry_times}")
    print(f"Retry Delay: {http_config.retry_delay}")
    print()

def test_redis_config():
    """测试Redis配置"""
    print("=== 测试 RedisConfig ===")
    redis_config = RedisConfig()
    print(f"Host: {redis_config.host}")
    print(f"Port: {redis_config.port}")
    print(f"DB: {redis_config.db}")
    print(f"URL: {redis_config.url}")
    print()

def test_log_config():
    """测试日志配置"""
    print("=== 测试 LogConfig ===")
    log_config = LogConfig()
    print(f"Level: {log_config.level}")
    print(f"Format: {log_config.format}")
    print(f"File Path: {log_config.file_path}")
    print(f"Max Size: {log_config.max_size}")
    print(f"Backup Count: {log_config.backup_count}")
    print()

def test_monitor_config():
    """测试监控配置"""
    print("=== 测试 MonitorConfig ===")
    monitor_config = MonitorConfig()
    print(f"Enable: {monitor_config.enable}")
    print(f"Interval: {monitor_config.interval}")
    print(f"Alert Threshold: {monitor_config.alert_threshold}")
    print()

def test_platform_config():
    """测试平台配置"""
    print("=== 测试 PlatformConfig ===")
    platform_config = PlatformConfig(
        platform_name="baidu",
        name="baidu",
        base_url="https://api.baidu.com"
    )
    print(f"Name: {platform_config.name}")
    print(f"Base URL: {platform_config.base_url}")
    print(f"Rate Limit: {platform_config.rate_limit}")
    print(f"Timeout: {platform_config.timeout}")
    print()

def test_app_config():
    """测试应用配置"""
    print("=== 测试 AppConfig ===")
    app_config = AppConfig()
    print(f"Debug: {app_config.app_debug}")
    print(f"Log Level: {app_config.app_log_level}")
    print(f"Environment: {app_config.app_env}")
    print(f"Database Host: {app_config.database.host}")
    print(f"HTTP Timeout: {app_config.http.timeout}")
    print(f"Redis Host: {app_config.redis.host}")
    print(f"Log Level: {app_config.log.level}")
    print(f"Monitor Enable: {app_config.monitor.enable}")
    print(f"Platforms: {list(app_config.platforms.keys())}")
    print()

if __name__ == "__main__":
    print("开始测试配置读取功能...\n")
    
    try:
        test_database_config()
        test_http_config()
        test_redis_config()
        test_log_config()
        test_monitor_config()
        test_platform_config()
        test_app_config()
        
        print("✅ 所有配置测试完成！")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()