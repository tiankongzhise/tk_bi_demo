from pydantic import BaseModel,Field,ConfigDict

class AdsQueryParams(BaseModel):
    start_time: str
    end_time: str
    report_type: str|int
    time_unit: str|int

class BdAdsQueryParams(BaseModel):
    controller_id:str|None = None
    controller_name:str
    columns:list[str]
    sorts:list[dict] = Field(default_factory=list)
    filters:list[dict] = Field(default_factory=list)
    startRow:int = 1
    rowCount:int = 1000
    needSum:bool = False
    
def to_camel_case(snake_str: str) -> str:
    """将下划线命名转换为驼峰命名"""
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])    
    
class BaiduAccessToken(BaseModel):
    access_token:str
    refresh_token:str
    open_id:str
    expires_time:str
    refresh_expires_time:str
    user_id:int
    
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel_case
    )
