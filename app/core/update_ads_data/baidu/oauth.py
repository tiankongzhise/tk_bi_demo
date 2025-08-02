import os
from datetime import datetime,timedelta

from ....logger import create_logger
from ....db import query_oauth_by_controler_id,query_oauth_by_controler_name,update_oauth_info
from ....utils import exceptions
from .http_client import refresh_access_http_client
logger = create_logger(__name__)


class BaiduOauthCore:
    def __init__(self,controler_name:str,controler_id:str|None = None,**kwargs):
        logger.info(f'BaiduOauthCore init!')
        logger.debug(f'controler_name:{controler_name},controler_id:{controler_id},kwargs:{kwargs}')
        self.controler_name = controler_name
        self.controler_id = controler_id
        self.kwargs = kwargs
    def get_access_token(self):
        if self.controler_id:
            oauth_info = query_oauth_by_controler_id(self.controler_id,'baidu')
        else:
            oauth_info = query_oauth_by_controler_name(self.controler_name,'baidu')
         # 防异常检测,如果同时存在controler_name和controler_id,优先使用controler_id进行查询,并且比对数据库中的controler_name和controler_id是否一致,
         # 不一致则保持与数据库中一致,并且发出warning日志
        if oauth_info:
            if oauth_info.controler_name != self.controler_name:
                self.controler_name = oauth_info.controler_name
                logger.warning(f'controler_name not match,controler_name:{self.controler_name},controler_name:{oauth_info.controler_name}')
        return oauth_info
    def refresh_access_token(self,oauth_info:dict):
        secret_key = os.getenv('BAIDU_OAUTH_SECRET_KEY')
        app_id = os.getenv('BAIDU_OAUTH_APP_ID')
        refresh_token = oauth_info['refresh_token']
        user_id = oauth_info['user_id']
        access_token = refresh_access_http_client(app_id,secret_key,refresh_token,user_id)
        return access_token
    def update_access_token(self,oauth_info:dict):
        update_oauth_info(self.controler_id,self.controler_name,'baidu',oauth_info)

    def oauth(self):
        oauth_info = self.get_access_token()
        if not oauth_info:
            logger.error(f'baidu oauth info not exist,controler_name:{self.controler_name},controler_id:{self.controler_id}')
            raise exceptions.AuthenticationException(
                message = 'baidu oauth info not exist',
                platform = 'baidu')
        # 如果token会在2小时内过期,则更新token,否则直接返回
        if oauth_info['refresh_expires_time']:
            refresh_expires_time = datetime.fromtimestamp(oauth_info['refresh_expires_time'])
            if refresh_expires_time < datetime.now() + timedelta(hours=2):
                access_token = self.refresh_access_token(oauth_info)
                oauth_info['access_token'] = access_token
                self.update_access_token(oauth_info)
        return oauth_info
