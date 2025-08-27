from sqlalchemy.orm import query
from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from ..kernel import BaiduHttpClient
from ..utils import camel_to_snake
from ..database import insert_baidu_keyword_daily,insert_baidu_keyword_hour
from ..models.base import ReturnModel

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
        # 验证start_time是否早于上个月的1月1日 00:00:00 只比较到秒
        if start_time_local < datetime.now().replace(day=1, month=datetime.now().month-1, hour=0, minute=0, second=0, microsecond=0):
            raise ValueError("get_changed_scale的start_time不能早于上个月的1月1日 00:00:00:00")
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
        self._changed_count = None
        self._start_time = None
        self._max_changed_count = 20000
        self._search_level_list = ['campaign','adgroup','keyword','creative','autoExpansion']
        self._feed_level_list = ['campaignFeed','adgroupFeed','creativeFeed','atpFeed']
        self._max_wait_time = 60
        self._max_re_cancel_count = 3
    
    def reset_core(self,access_token:str,user_name:str,temp_dir:str):
        self.config_settings = get_config_settings()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
        self._changed_count = None
        self._start_time = None
        self._max_changed_count = 20000
        
    def get_changed_scale(self):
        """获取变更规模"""
        if self._start_time is None:
            self._start_time = Utils.get_last_month_time()
        if not Utils.filed_valid_start_time(self._start_time):
            raise ValueError(f"get_changed_scale的start_time格式错误,要求为%Y-%m-%d或者%Y-%m-%d HH:MM:SS,当前为{self._start_time}")
        rsp = self.http_client.get_changed_scale(self._start_time)
        changed_data:dict[str,list] = rsp.get('body',{}).get('data',[{}])[0]
        changed_count = 0
        for key,value in changed_data.items():
            if 'Scale' in key:
                changed_count += value[0]
        return changed_count
            
    
    def get_changed_objects(self,query_params:dict|None = None):
        """增量下载"""
        if query_params is None:
            query_params = {
                'mobileExtend':1
            }
            query_params.update({
                f'{level}Fields':['all'] for level in self._search_level_list
            })
            query_params['businessLabelFields'] = ['all']
        
        if self._start_time is None:
            self._start_time = Utils.get_last_month_time()
        try:
            rsp = self.http_client.get_all_changed_objects(self._start_time,**query_params)
            if rsp.get('body',{}).get('data',[{}])[0].get('fileId'):
                logger.info_core(f"{self.user_name}增量下载成功,响应数据: {rsp}")
                return ReturnModel(status='success',
                                   message=f'百度渠道,账户:{self.user_name},账户变化增量任务创建成功',
                                   data=rsp.get('body',{}).get('data',[{}])[0].get('fileId'))
            else:
                logger.info_core(f"{self.user_name}增量下载返回异常,响应数据: {rsp}")
                return ReturnModel(status='error',
                                   message=f'百度渠道,账户:{self.user_name},账户变化增量任务创建异常,响应数据: {rsp}',
                                   data=None)
        except Exception as e:
            logger.error(f"{self.user_name}增量下载失败,异常信息: {e}")
            return ReturnModel(status='error',
                               message=f'百度渠道,账户:{self.user_name},账户变化增量任务创建异常,异常信息: {e}',
                               data=None)
    
    def get_all_objects(self):
        """全量下载"""
        pass
    
    def get_objects_status(self,file_id:str):
        """查询文件状态"""
        wait_time = 0
        while True:
            rsp = self.http_client.get_file_status(file_id)
            file_status = rsp.get('body',{}).get('data',[{}])[0].get('isGenerated')
            if file_status == 3:
                return ReturnModel(status='success',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},状态查询成功,文件已生成',
                                data=file_id)
            elif file_status == 5:
                self.cancel_download(file_id)
                return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},部分成功,响应数据: {rsp}',
                                data=None)
            else:
                logger.info_core(f"百度渠道,账户:{self.user_name},文件ID:{file_id},状态查询生产中,响应数据: {rsp},延迟5秒再查询")
                time.sleep(5)
                wait_time += 5
                if wait_time > self._max_wait_time:
                    self.cancel_download(file_id)
                    return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},状态查询超时,响应数据: {rsp}',
                                data=None)
    
    def get_objects_file_path(self,file_id:str):
        """获取文件下载地址"""
        try:
            rsp = self.http_client.get_file_path(file_id)
            file_path = rsp.get('body',{}).get('data',[{}])[0]
            if file_path:
                return ReturnModel(status='success',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},获取文件下载地址成功,响应数据: {rsp}',
                                data=file_path)
            else:
                return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},获取文件下载地址失败,响应数据: {rsp}',
                                data=None)
        except Exception as e:
            logger.error(f"获取文件下载地址失败,异常信息: {e}")
            return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},获取文件下载地址失败,异常信息: {e}',
                                data=None)
    
    def download_objects(self,file_path:dict):
        """下载文件"""
        ...
    
    def cancel_download(self,file_id:str):
        """取消下载"""
        re_cancel_time = 0
        while True:
            rsp = self.http_client.cancel_download(file_id)
            if rsp.get('body',{}).get('data',[{}])[0].get('isCancelled') == 3:
                return ReturnModel(status='success',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},取消下载成功,响应数据: {rsp}',
                                data=file_id)
            else:
                logger.info_core(f"百度渠道,账户:{self.user_name},文件ID:{file_id},取消下载失败,响应数据: {rsp},延迟5秒再取消,目前已重试{re_cancel_time}次")
                time.sleep(5)
                re_cancel_time += 1
                if re_cancel_time > self._max_re_cancel_count:
                    return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},取消下载失败,响应数据: {rsp}',
                                data=file_id)
    

    
    def choose_get_objects_function(self):
        """选择全量下载还是增量下载"""
        changed_count = self.get_changed_scale(self._start_time)
        if changed_count > self._max_changed_count:
            logger.info_core(f"变更数据量{changed_count}大于{self._max_changed_count},选择全量下载")
            return self.get_all_objects
        else:
            logger.info_core(f"变更数据量{changed_count}小于{self._max_changed_count},选择增量下载")
            return self.get_changed_objects
        
    
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

