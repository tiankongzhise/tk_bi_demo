from pydantic import BaseModel, ConfigDict, field_validator
from ..utils import to_camel
from typing import TypeVar,Generic,Literal
T = TypeVar('T')



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


class ReturnModel(BaseModel, Generic[T]):
    """
    通用返回模型
    支持自定义数据类型T，用于返回具体数据
    支持自定义状态码status，支持success/error,大小写不敏感
    支持自定义消息message，用于返回提示信息
    支持自定义数据data，用于返回具体数据
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str
    message: str
    data: T|None = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """验证 status 字段，支持大小写不敏感"""
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ['success', 'error']:
                return v_lower
        raise ValueError(f"status must be 'success' or 'error', got: {v}")
