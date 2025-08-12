import functools
import inspect
import re

from .trans import camel_to_snake


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
            param_names = []  # 除self外的参数名列表，按顺序
            
            # 构建格式转换映射表和参数名列表
            for name, param in sig.parameters.items():
                if name == 'self':
                    continue
                param_names.append(name)
                camel_name = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
                param_map[name] = name  # 原始下划线格式
                param_map[camel_name] = name  # 小驼峰格式映射
            
            # 先从*args按位置读取参数
            normalized_kwargs = {}
            for i, arg_value in enumerate(args):
                if i < len(param_names):
                    param_name = param_names[i]
                    normalized_kwargs[param_name] = arg_value
            
            # 再处理kwargs中的参数（如果args中没有提供或值为None）
            for key, value in kwargs.items():
                # 优先使用原始传入的键
                normalized_key = param_map.get(key, key)
                # 只有当参数不存在或为None时，才从kwargs中获取
                if normalized_key not in normalized_kwargs or normalized_kwargs[normalized_key] is None:
                    normalized_kwargs[normalized_key] = value
            
            # 检查必填参数
            missing = []
            for param in required_params:
                if param not in normalized_kwargs or normalized_kwargs[param] is None:
                    missing.append(param)
            
            if missing:
                raise TypeError(f"Missing required parameters: {', '.join(missing)}")
            
            # 绑定并调用原始函数
            bound = sig.bind(self, **normalized_kwargs)
            bound.apply_defaults()
            return func(*bound.args, **bound.kwargs)
        
        return wrapper
    return decorator
