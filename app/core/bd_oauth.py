import os
from datetime import datetime,timedelta
import httpx

from ..logger import create_logger
from ..models import BaiduAccessToken
from ..database import query_oauth_by_controler_id,query_oauth_by_controler_name,update_oauth_info
from ..utils import exceptions,retry
from ..config import get_config_settings
logger = create_logger(__name__)


@retry()
def refresh_access_http_client(app_id:str,secret_key:str,refresh_token:str,user_id:str):
    with httpx.Client() as client:
        url = "https://u.baidu.com/oauth/refreshToken"
        headers = {
            "Content-Type": "application/json;charset:utf-8;",
        }
        params = {
            "appId": app_id,
            "refreshToken": refresh_token,
            "secretKey": secret_key,
            "userId": user_id,
        }
        response = client.post(url, headers=headers, json=params)
        response.raise_for_status()
        return response.json()


class BaiduOauthCore:
    def __init__(self,controler_name:str,controler_id:str|None = None,**kwargs):
        logger.info_core('BaiduOauthCore init!')
        logger.info_core(f'controler_name:{controler_name},controler_id:{controler_id},kwargs:{kwargs}')
        self.controler_name = controler_name
        self.controler_id = controler_id
        self.kwargs = kwargs
        if kwargs.get('config_settings'):
            self.config_settings = kwargs.get('config_settings')
        else:
            self.config_settings = get_config_settings()
        
    def get_access_token(self):
        if self.controler_id:
            oauth_info = query_oauth_by_controler_id(self.controler_id,'baidu')
        else:
            oauth_info = query_oauth_by_controler_name(self.controler_name,'baidu')
         # 防异常检测,如果同时存在controler_name和controler_id,优先使用controler_id进行查询,并且比对数据库中的controler_name和controler_id是否一致,
         # 不一致则保持与数据库中一致,并且发出warning日志
        if oauth_info:
            # 设置controler_id，确保后续操作有正确的ID
            if not self.controler_id:
                self.controler_id = oauth_info.controler_id
            if oauth_info.controler_name != self.controler_name:
                self.controler_name = oauth_info.controler_name
                logger.warning(f'controler_name not match,controler_name:{self.controler_name},controler_name:{oauth_info.controler_name}')
        return oauth_info
    def refresh_access_token(self,oauth_info:dict):
        secret_key = os.getenv('BAIDU_OAUTH_SECRET_KEY')
        app_id = os.getenv('BAIDU_OAUTH_APP_ID')
        refresh_token = oauth_info['refresh_token']
        user_id = oauth_info['user_id']
        try:
            rsp = refresh_access_http_client(app_id,secret_key,refresh_token,user_id)
            access_token = BaiduAccessToken(**rsp['data'])
        except httpx.HTTPError as e:
            logger.error(f'baidu oauth refresh token error,error:{e}')
            raise exceptions.AuthenticationException(
                message = 'baidu oauth refresh token error',
                platform = 'baidu')
        except KeyError as e:
            logger.error(f'baidu oauth refresh token error,error:{e}')
            raise exceptions.AuthenticationException(
                message = 'baidu oauth refresh token error',
                platform = 'baidu')
        except Exception as e:
            logger.error(f'baidu oauth refresh token error,error:{e}')
            raise exceptions.AuthenticationException(
                message = 'baidu oauth refresh token error',
                platform = 'baidu')
            
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

        expires_time = datetime.strptime(oauth_info.oauth_credentials['expires_time'],'%Y-%m-%d %H:%M:%S')
        if expires_time > datetime.now() + timedelta(hours=self.config_settings.baidu_oauth_config.get('refresh_token_time_delta',2)):
            return BaiduAccessToken(**oauth_info.oauth_credentials)
            
        new_oauth_info = self.refresh_access_token(oauth_info.oauth_credentials)
        self.update_access_token(new_oauth_info.model_dump())
        return new_oauth_info
