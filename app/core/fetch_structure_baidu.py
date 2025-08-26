from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from ..kernel import BaiduHttpClient
from ..utils import camel_to_snake
from ..database import insert_baidu_keyword_daily,insert_baidu_keyword_hour

from tk_base_utils.tk_http.exceptions import TimeoutError,HttpClientError
from pathlib import Path
from typing import Generator

import time
from datetime import datetime
logger = create_logger(__name__)

class FetchStructureBaiduCore:
    def __init__(self,access_token:str,user_name:str,temp_dir:str) -> None:
        self.config_settings = get_config_settings()
        self.http_client = BaiduHttpClient()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
    
    def get_changed_scale(self):
        """获取变更规模"""
        pass
    
    def get_changed_objects(self):
        """增量下载"""
        pass
    
    def get_all_objects(self):
        """全量下载"""
        pass
    
    def get_objects_status(self):
        """查询文件状态"""
        pass
    
    def get_objects_file_path(self):
        """获取文件下载地址"""
        pass
    def download_objects(self):
        """下载文件"""
        pass
    
    def cancel_download(self):
        """取消下载"""
        pass
    
    def choose_get_objects_function(self):
        """选择全量下载还是增量下载"""
        pass
    def create_objects_task(self):
        """创建下载任务"""
        pass


    def run(self):
        """运行"""
        self.get_changed_scale()
        self.choose_get_objects_function()
        self.create_objects_task()
        self.get_objects_status()
        self.get_objects_file_path()
        self.download_objects()

