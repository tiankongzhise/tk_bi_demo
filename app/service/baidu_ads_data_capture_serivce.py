from ..utils import (
    AdsDataCaptureFactory
)
from ..core import BaiduOauthCore,FetchAdsDataBaiduCore
from ..config import get_config_settings



class BaiduAdsDataCaptureService(AdsDataCaptureFactory):
    def __init__(self,controller_name:str|None = None,controller_id:str|None = None) -> None:
        self.config_settings = get_config_settings()
        self.controller_name = controller_name or self.config_settings.baidu_oauth_config.get('controller_name')
        self.controller_id = controller_id or self.config_settings.baidu_oauth_config.get('controller_id')

    def oauth(self):
        oauth_core = BaiduOauthCore(self.controller_name,self.controller_id)
        oauth_credentials = oauth_core.oauth()
        self.access_token = oauth_credentials.access_token
        return self
    def get_ads_report_data(self,user_name:str,report_name:str):
        if not hasattr(self,'access_token'):
            self.oauth()
        fetch_ads_data_baidu_core = FetchAdsDataBaiduCore(self.access_token,user_name)
        report_task = fetch_ads_data_baidu_core.create_report_task(report_name)
        return report_task
        
    def get_ads_account_structure(self):
        pass
    def update_ads_data(self):
        pass
    def update_ads_account_structure(self):
        pass
    def notify_result(self):
        pass
    def run(self):
        pass
