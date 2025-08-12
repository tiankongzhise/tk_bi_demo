import re

# 转换函数：下划线转小驼峰
def to_camel(field: str) -> str:
    """
    将 snake_case 转换为 camelCase
    示例：user_name -> userName, api_key -> apiKey
    """
    words = field.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])

def camel_to_snake(name):
    """将小驼峰格式转换为下划线格式"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
