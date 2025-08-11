# 转换函数：下划线转小驼峰
def to_camel(field: str) -> str:
    """
    将 snake_case 转换为 camelCase
    示例：user_name -> userName, api_key -> apiKey
    """
    words = field.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])
