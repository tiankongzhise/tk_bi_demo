from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from .baidu_http_core import BaiduHttpClient
from ..utils import accept_both_cases


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
        self.user_name = user_name

    @logger_wrapper()
    def create_report_task(self,report_name:str):
        report_params = self.config_settings.get_baidu_report_config(report_name)
        response = self.http_client.create_report_task(**report_params)
        logger.info(f"{self.user_name}创建报告任务响应: {response}")
        if response.get('header',{}).get('desc','') == 'success':
            try:
                task_id = response['body']['data'][0]['taskId']
                self.task_id = task_id
            except (KeyError,IndexError) as e:
                logger.error(f"{self.user_name}创建报告任务失败,响应数据异常: {e},response:{response}")
                raise
            logger.info(f"{self.user_name}创建报告任务成功,任务ID: {task_id}")
            return task_id
        else:
            logger.error(f"{self.user_name}创建报告任务失败,响应数据异常: {response}")
            raise


    def get_task_status(self,task_id:str|int):
        response = self.http_client.get_report_task_status(task_id)
        logger.info(f"{self.user_name}获取报告任务状态响应: {response}")
        return response
    def fetch_report_data(self):
        pass
    def process_report_data(self):
        pass
    def save_report_data(self):
        pass
    def run(self,report_name:str):
        task_id = self.create_report_task(report_name)
        self.get_task_status(task_id)
        self.fetch_report_data()
        self.process_report_data()
        self.save_report_data()
    


