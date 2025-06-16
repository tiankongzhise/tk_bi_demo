"""数据验证工具模块

提供各种数据验证功能。
"""

import re
import ipaddress
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse

from ..core import get_logger
from ..models.schemas import PlatformEnum

logger = get_logger(__name__)


class ValidationError(Exception):
    """验证错误异常"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.field:
            return f"字段 '{self.field}' 验证失败: {self.message}"
        return self.message


class DataValidator:
    """数据验证器
    
    提供各种数据验证方法。
    """
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        if not email or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """验证URL格式
        
        Args:
            url: URL地址
            
        Returns:
            bool: 是否有效
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """验证IP地址格式
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否有效
        """
        if not ip or not isinstance(ip, str):
            return False
        
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_phone(phone: str, country_code: str = "CN") -> bool:
        """验证手机号格式
        
        Args:
            phone: 手机号
            country_code: 国家代码
            
        Returns:
            bool: 是否有效
        """
        if not phone or not isinstance(phone, str):
            return False
        
        # 移除所有非数字字符
        clean_phone = re.sub(r'\D', '', phone)
        
        if country_code == "CN":
            # 中国手机号验证
            pattern = r'^1[3-9]\d{9}$'
            return bool(re.match(pattern, clean_phone))
        
        # 其他国家的简单验证（7-15位数字）
        return 7 <= len(clean_phone) <= 15
    
    @staticmethod
    def is_valid_date_string(date_string: str, format_str: str = "%Y-%m-%d") -> bool:
        """验证日期字符串格式
        
        Args:
            date_string: 日期字符串
            format_str: 日期格式
            
        Returns:
            bool: 是否有效
        """
        if not date_string or not isinstance(date_string, str):
            return False
        
        try:
            datetime.strptime(date_string, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_platform(platform: str) -> bool:
        """验证平台名称
        
        Args:
            platform: 平台名称
            
        Returns:
            bool: 是否有效
        """
        if not platform or not isinstance(platform, str):
            return False
        
        try:
            PlatformEnum(platform)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_positive_number(value: Union[int, float]) -> bool:
        """验证是否为正数
        
        Args:
            value: 数值
            
        Returns:
            bool: 是否为正数
        """
        try:
            return isinstance(value, (int, float)) and value > 0
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def is_non_negative_number(value: Union[int, float]) -> bool:
        """验证是否为非负数
        
        Args:
            value: 数值
            
        Returns:
            bool: 是否为非负数
        """
        try:
            return isinstance(value, (int, float)) and value >= 0
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def is_valid_percentage(value: Union[int, float]) -> bool:
        """验证是否为有效百分比（0-100）
        
        Args:
            value: 数值
            
        Returns:
            bool: 是否为有效百分比
        """
        try:
            return isinstance(value, (int, float)) and 0 <= value <= 100
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def is_valid_json_string(json_string: str) -> bool:
        """验证JSON字符串格式
        
        Args:
            json_string: JSON字符串
            
        Returns:
            bool: 是否有效
        """
        if not json_string or not isinstance(json_string, str):
            return False
        
        try:
            import json
            json.loads(json_string)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """验证必填字段
        
        Args:
            data: 数据字典
            required_fields: 必填字段列表
            
        Returns:
            List[str]: 缺失的字段列表
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> List[str]:
        """验证字段类型
        
        Args:
            data: 数据字典
            field_types: 字段类型映射
            
        Returns:
            List[str]: 类型错误的字段列表
        """
        type_errors = []
        
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    type_errors.append(f"{field} (期望: {expected_type.__name__}, 实际: {type(data[field]).__name__})")
        
        return type_errors


class SchemaValidator:
    """模式验证器
    
    提供基于模式的数据验证功能。
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """初始化模式验证器
        
        Args:
            schema: 验证模式
        """
        self.schema = schema
        self.validator = DataValidator()
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据
        
        Args:
            data: 要验证的数据
            
        Returns:
            Dict[str, Any]: 验证结果
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        errors = []
        warnings = []
        
        # 验证必填字段
        required_fields = self.schema.get("required", [])
        missing_fields = self.validator.validate_required_fields(data, required_fields)
        if missing_fields:
            errors.extend([f"缺少必填字段: {field}" for field in missing_fields])
        
        # 验证字段类型
        field_types = self.schema.get("types", {})
        type_errors = self.validator.validate_field_types(data, field_types)
        if type_errors:
            errors.extend([f"字段类型错误: {error}" for error in type_errors])
        
        # 验证字段值
        field_validators = self.schema.get("validators", {})
        for field, validator_config in field_validators.items():
            if field in data and data[field] is not None:
                field_errors = self._validate_field(field, data[field], validator_config)
                errors.extend(field_errors)
        
        # 验证字段范围
        field_ranges = self.schema.get("ranges", {})
        for field, range_config in field_ranges.items():
            if field in data and data[field] is not None:
                range_errors = self._validate_range(field, data[field], range_config)
                errors.extend(range_errors)
        
        # 验证字段长度
        field_lengths = self.schema.get("lengths", {})
        for field, length_config in field_lengths.items():
            if field in data and data[field] is not None:
                length_errors = self._validate_length(field, data[field], length_config)
                errors.extend(length_errors)
        
        # 验证自定义规则
        custom_validators = self.schema.get("custom", {})
        for field, custom_validator in custom_validators.items():
            if field in data and data[field] is not None:
                try:
                    if not custom_validator(data[field]):
                        errors.append(f"字段 '{field}' 未通过自定义验证")
                except Exception as e:
                    errors.append(f"字段 '{field}' 自定义验证器执行失败: {str(e)}")
        
        # 检查未知字段
        if self.schema.get("strict", False):
            allowed_fields = set(self.schema.get("types", {}).keys())
            allowed_fields.update(self.schema.get("validators", {}).keys())
            allowed_fields.update(self.schema.get("ranges", {}).keys())
            allowed_fields.update(self.schema.get("lengths", {}).keys())
            allowed_fields.update(self.schema.get("custom", {}).keys())
            
            unknown_fields = set(data.keys()) - allowed_fields
            if unknown_fields:
                warnings.extend([f"未知字段: {field}" for field in unknown_fields])
        
        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data": data
        }
        
        if errors:
            logger.warning(
                "数据验证失败",
                extra={
                    "errors": errors,
                    "warnings": warnings,
                    "data_keys": list(data.keys())
                }
            )
        
        return result
    
    def _validate_field(self, field: str, value: Any, validator_config: Dict[str, Any]) -> List[str]:
        """验证单个字段
        
        Args:
            field: 字段名
            value: 字段值
            validator_config: 验证器配置
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        validator_type = validator_config.get("type")
        
        if validator_type == "email":
            if not self.validator.is_valid_email(value):
                errors.append(f"字段 '{field}' 不是有效的邮箱地址")
        
        elif validator_type == "url":
            if not self.validator.is_valid_url(value):
                errors.append(f"字段 '{field}' 不是有效的URL")
        
        elif validator_type == "ip":
            if not self.validator.is_valid_ip(value):
                errors.append(f"字段 '{field}' 不是有效的IP地址")
        
        elif validator_type == "phone":
            country_code = validator_config.get("country_code", "CN")
            if not self.validator.is_valid_phone(value, country_code):
                errors.append(f"字段 '{field}' 不是有效的手机号")
        
        elif validator_type == "date":
            date_format = validator_config.get("format", "%Y-%m-%d")
            if not self.validator.is_valid_date_string(value, date_format):
                errors.append(f"字段 '{field}' 不是有效的日期格式")
        
        elif validator_type == "platform":
            if not self.validator.is_valid_platform(value):
                errors.append(f"字段 '{field}' 不是有效的平台名称")
        
        elif validator_type == "positive":
            if not self.validator.is_positive_number(value):
                errors.append(f"字段 '{field}' 必须是正数")
        
        elif validator_type == "non_negative":
            if not self.validator.is_non_negative_number(value):
                errors.append(f"字段 '{field}' 必须是非负数")
        
        elif validator_type == "percentage":
            if not self.validator.is_valid_percentage(value):
                errors.append(f"字段 '{field}' 必须是0-100之间的百分比")
        
        elif validator_type == "json":
            if not self.validator.is_valid_json_string(value):
                errors.append(f"字段 '{field}' 不是有效的JSON字符串")
        
        elif validator_type == "regex":
            pattern = validator_config.get("pattern")
            if pattern and not re.match(pattern, str(value)):
                errors.append(f"字段 '{field}' 不匹配正则表达式模式")
        
        return errors
    
    def _validate_range(self, field: str, value: Any, range_config: Dict[str, Any]) -> List[str]:
        """验证字段范围
        
        Args:
            field: 字段名
            value: 字段值
            range_config: 范围配置
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        try:
            min_val = range_config.get("min")
            max_val = range_config.get("max")
            
            if min_val is not None and value < min_val:
                errors.append(f"字段 '{field}' 的值 {value} 小于最小值 {min_val}")
            
            if max_val is not None and value > max_val:
                errors.append(f"字段 '{field}' 的值 {value} 大于最大值 {max_val}")
        
        except (TypeError, ValueError):
            errors.append(f"字段 '{field}' 无法进行范围比较")
        
        return errors
    
    def _validate_length(self, field: str, value: Any, length_config: Dict[str, Any]) -> List[str]:
        """验证字段长度
        
        Args:
            field: 字段名
            value: 字段值
            length_config: 长度配置
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        try:
            length = len(value)
            min_length = length_config.get("min")
            max_length = length_config.get("max")
            
            if min_length is not None and length < min_length:
                errors.append(f"字段 '{field}' 的长度 {length} 小于最小长度 {min_length}")
            
            if max_length is not None and length > max_length:
                errors.append(f"字段 '{field}' 的长度 {length} 大于最大长度 {max_length}")
        
        except TypeError:
            errors.append(f"字段 '{field}' 无法计算长度")
        
        return errors


# 预定义的验证模式
AD_DATA_SCHEMA = {
    "required": ["platform", "account_id", "campaign_id", "report_date"],
    "types": {
        "platform": str,
        "account_id": str,
        "campaign_id": str,
        "report_date": str,
        "impressions": int,
        "clicks": int,
        "cost": float,
        "conversions": int
    },
    "validators": {
        "platform": {"type": "platform"},
        "report_date": {"type": "date", "format": "%Y-%m-%d"},
        "impressions": {"type": "non_negative"},
        "clicks": {"type": "non_negative"},
        "cost": {"type": "non_negative"},
        "conversions": {"type": "non_negative"}
    },
    "ranges": {
        "cost": {"min": 0, "max": 1000000}
    },
    "lengths": {
        "account_id": {"min": 1, "max": 100},
        "campaign_id": {"min": 1, "max": 100}
    }
}

TASK_CONFIG_SCHEMA = {
    "required": ["task_name", "platform", "task_type"],
    "types": {
        "task_name": str,
        "platform": str,
        "task_type": str,
        "schedule": str,
        "enabled": bool,
        "retry_count": int,
        "timeout": int
    },
    "validators": {
        "platform": {"type": "platform"},
        "retry_count": {"type": "non_negative"},
        "timeout": {"type": "positive"}
    },
    "ranges": {
        "retry_count": {"min": 0, "max": 10},
        "timeout": {"min": 1, "max": 3600}
    },
    "lengths": {
        "task_name": {"min": 1, "max": 100}
    }
}


def create_validator(schema: Dict[str, Any]) -> SchemaValidator:
    """创建验证器
    
    Args:
        schema: 验证模式
        
    Returns:
        SchemaValidator: 验证器实例
    """
    return SchemaValidator(schema)


def validate_ad_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证广告数据
    
    Args:
        data: 广告数据
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    validator = create_validator(AD_DATA_SCHEMA)
    return validator.validate(data)


def validate_task_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证任务配置
    
    Args:
        data: 任务配置数据
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    validator = create_validator(TASK_CONFIG_SCHEMA)
    return validator.validate(data)