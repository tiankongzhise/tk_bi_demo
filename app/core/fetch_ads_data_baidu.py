from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from .baidu_http_core import BaiduHttpClient


logger = create_logger(__name__)




class FetchAdsDataBaiduCore:
    """
    百度广告数据获取核心类
    """
    @logger_wrapper()
    def __init__(self,access_token:str,user_name:str) -> None:
        self.config_settings = get_config_settings()
        self.http_client = BaiduHttpClient()
        self.http_client.set_oauth_account(user_name,access_token)


        
    @logger_wrapper()
    def create_report_task(self,report_name:str):
        report_params = self.config_settings.get_baidu_report_config(report_name)
        response = self.http_client.create_report_task(**report_params)
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
    


