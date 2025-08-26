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

class Utils(object):
    @staticmethod
    def _is_time_valid(time_str:str):
        try:
            datetime.strptime(time_str, "%Y-%m-%d")
            return True
        except ValueError:
            pass
        try:
            datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            pass
        return False
    @staticmethod
    # 验证get_changed_scale的start_time入参是否合规,要求为满足%Y-%m-%d或者%Y-%m-%d HH:MM:SS 且时间以现在为起点不能早于上个月的1月1日
    def filed_valid_start_time(start_time:str|None = None):
        if start_time is None:
            raise ValueError("get_changed_scale的start_time为空,出现意料之外的错误")
        if not Utils._is_time_valid(start_time):
            raise ValueError("get_changed_scale的start_time格式错误,要求为%Y-%m-%d或者%Y-%m-%d HH:MM:SS")
        try:
            start_time_local = datetime.strptime(start_time, "%Y-%m-%d")
        except ValueError:
            start_time_local = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if start_time_local < datetime.now().replace(day=1, month=datetime.now().month-1):
            raise ValueError("get_changed_scale的start_time不能早于上个月的1月1日")
        return True

    @staticmethod
    def get_last_month_time():
        """获取上个月的时间"""
        last_month = datetime.now().month - 1
        last_year = datetime.now().year
        if last_month == 0:
            last_month = 12
            last_year -= 1
        return f"{last_year}-{last_month}-01"

class FetchStructureBaiduCore:
    def __init__(self,access_token:str,user_name:str,temp_dir:str) -> None:
        self.config_settings = get_config_settings()
        self.http_client = BaiduHttpClient()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
    
    def reset_core(self,access_token:str,user_name:str,temp_dir:str):
        self.config_settings = get_config_settings()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
        
    def get_changed_scale(self,start_time:str|None = None):
        """获取变更规模"""
        if start_time is None:
            start_time = Utils.get_last_month_time()
        if not Utils.filed_valid_start_time(start_time):
            raise ValueError(f"get_changed_scale的start_time格式错误,要求为%Y-%m-%d或者%Y-%m-%d HH:MM:SS,当前为{start_time}")
        rsp = self.http_client.get_changed_scale(start_time)
        changed_data:dict[str,list] = rsp.get('body',{}).get('data',[{}])[0]
        changed_count = 0
        for key,value in changed_data.items():
            if 'Scale' in key:
                changed_count += value[0]
        return changed_count
            
    
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

