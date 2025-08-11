import functools
import inspect
import re

def camel_to_snake(name):
    """将小驼峰格式转换为下划线格式"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def accept_both_cases(*required_params):
    """
    装饰器工厂函数，支持参数名格式自动转换
    :param required_params: 必须传入的参数名（以下划线格式）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 创建参数格式转换映射
            sig = inspect.signature(func)
            param_map = {}
            
            # 构建格式转换映射表
            for name, param in sig.parameters.items():
                if name == 'self':
                    continue
                camel_name = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
                param_map[name] = name  # 原始下划线格式
                param_map[camel_name] = name  # 小驼峰格式映射
            
            # 转换参数格式并合并
            normalized_kwargs = {}
            for key, value in kwargs.items():
                # 优先使用原始传入的键
                normalized_key = param_map.get(key, key)
                normalized_kwargs[normalized_key] = value
            
            # 检查必填参数
            missing = []
            for param in required_params:
                if param not in normalized_kwargs:
                    missing.append(param)
            
            if missing:
                raise TypeError(f"Missing required parameters: {', '.join(missing)}")
            
            # 绑定并调用原始函数
            bound = sig.bind(self, *args, **normalized_kwargs)
            bound.apply_defaults()
            return func(*bound.args, **bound.kwargs)
        
        return wrapper
    return decorator
