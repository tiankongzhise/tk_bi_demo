from pydantic import BaseModel, ConfigDict
from ..utils import to_camel




# 基类模型配置（复用配置）
class CamelCaseBase(BaseModel):
    """基础模型：自动处理小驼峰输入输出"""
    
    model_config = ConfigDict(
        # 关键配置：允许通过别名创建模型实例
        populate_by_name = True,
        
        # 别名生成器：将字段名转为小驼峰格式
        alias_generator = to_camel,
        
        # 序列化时也使用别名（输出小驼峰）
        json_encoders = {dict: lambda d: {to_camel(k): v for k, v in d.items()}}
    )
