from doctest import REPORT_CDIFF
import os
from datetime import datetime,timedelta
import httpx
from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from ..utils import retry

logger = create_logger(__name__)




class FetchAdsDataBaiduCore:
    """
    百度广告数据获取核心类
    """
    @logger_wrapper()
    def __init__(self,access_token:str,user_name:str) -> None:
        self.config_settings = get_config_settings()
        self.http_headers = {
            "Content-Type": "application/json;charset:utf-8;",
        }
        self.query_headers = {
            "userName":user_name,
            "accessToken":access_token,
        }
    @retry(max_attempts=3, delay=1, exceptions=(httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError))
    def _http_request(self,method:str,url:str,params:dict|None = None,json:dict|None = None):
        """发送HTTP请求，遇到网络连接抖动造成的超时时自动重试"""
        timeout = httpx.Timeout(30.0, connect=10.0)  # 总超时30秒，连接超时10秒
        with httpx.Client(timeout=timeout) as client:
            response = client.request(method,url,params=params,json=json,headers=self.http_headers)
            response.raise_for_status()
            return response.json()
    @logger_wrapper()
    def create_report_task(self,report_name:str):
        url = 'https://api.baidu.com/json/sms/service/OpenApiReportService/createReportTask'
        report_params = self.config_settings.get_baidu_report_config(report_name)
        if not report_params:
            return
        json_params = {
            "header":self.query_headers,
            "body":report_params
        }
        response = self._http_request('POST',url,json=json_params)
        logger.info(f"创建报告任务响应: {response}")

        return response
    def get_task_status(self):
        pass
    def fetch_report_data(self):
        pass
    def process_report_data(self):
        pass
    def save_report_data(self):
        pass
    def run(self):
        self.create_report_task()
        self.get_task_status()
        self.fetch_report_data()
        self.process_report_data()
        self.save_report_data()
    


