from .base import CamelCaseBase
class BaiduAccessToken(CamelCaseBase):
    access_token:str
    refresh_token:str
    open_id:str
    expires_time:str
    refresh_expires_time:str
    user_id:int
    