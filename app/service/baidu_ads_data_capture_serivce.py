from ..utils import (
    AdsDataCaptureFactory
)
from ..core import BaiduOauthCore,FetchAdsDataBaiduCore
from ..config import get_config_settings
from ..logger import create_logger

logger = create_logger(__name__)




class BaiduAdsDataCaptureService(AdsDataCaptureFactory):
    def __init__(self,controller_name:str|None = None,controller_id:str|None = None) -> None:
        self.config_settings = get_config_settings()
        self.controller_name = controller_name or self.config_settings.baidu_oauth_config.get('controller_name')
        self.controller_id = controller_id or self.config_settings.baidu_oauth_config.get('controller_id')

    def oauth(self):
        oauth_core = BaiduOauthCore(self.controller_name,self.controller_id)
        oauth_credentials = oauth_core.oauth()
        self.access_token = oauth_credentials.access_token
        logger.info(f"获取到的百度广告账户{self.controller_name}的access_token为:{self.access_token}")
        return self
    
    def get_ads_report_data(self):
        user_name_list = self.config_settings.baidu_user_name_list
        report_name_list = self.config_settings.baidu_report_name_list
        temp_dir = self.config_settings.temp_dir
        for user_name in user_name_list:
            for report_name in report_name_list:
                fetch_ads_data_baidu_core = FetchAdsDataBaiduCore(self.access_token,user_name,temp_dir)
                fetch_ads_data_baidu_core.run(report_name)
                logger.info(f"获取百度广告账户{self.controller_name}的用户{user_name}的报告{report_name}的数据结束")
        return self




        
    def get_ads_account_structure(self):
        pass
    def update_ads_data(self):
        pass
    def update_ads_account_structure(self):
        pass
    def notify_result(self):
        pass
    def run(self):
        self.oauth().get_ads_report_data()


