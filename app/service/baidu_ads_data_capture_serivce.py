from ..utils import (
    AdsDataCaptureFactory
)
from ..core import BaiduOauthCore,FetchAdsDataBaiduCore
from ..config import get_config_settings
from ..logger import create_logger,logger_wrapper
from ..models.base import ReturnModel
from .baidu_structure_zipper_service import BaiduStructureZipperService

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
        logger.info_service(f"获取到的百度广告账户{self.controller_name}的access_token为:{self.access_token}")
        return self
    
    def get_ads_report_data(self):
        user_name_list = self.config_settings.baidu_user_name_list
        report_name_list = self.config_settings.baidu_report_name_list
        temp_dir = self.config_settings.temp_dir
        for user_name in user_name_list:
            for report_name in report_name_list:
                fetch_ads_data_baidu_core = FetchAdsDataBaiduCore(self.access_token,user_name,temp_dir)
                fetch_ads_data_baidu_core.run(report_name)
                logger.info_service(f"获取百度广告账户{self.controller_name}的用户{user_name}的报告{report_name}的数据结束")
        return self




        
    def get_ads_account_structure(self, user_id: str, account_id: str):
        """获取广告账户结构数据（全量）"""
        temp_dir = self.config_settings.temp_dir
        structure_service = BaiduStructureZipperService(
            access_token=self.access_token,
            user_id=user_id,
            temp_dir=temp_dir
        )
        result = structure_service.full_update_structure_data(user_id, account_id)
        logger.info_service(f"获取百度广告账户{user_id}的结构数据结束，结果: {result.message}")
        return result
    
    def update_ads_data(self):
        """更新广告数据（报告数据）"""
        return self.get_ads_report_data()
    
    def update_ads_account_structure(self, user_id: str, account_id: str):
        """增量更新广告账户结构数据"""
        temp_dir = self.config_settings.temp_dir
        structure_service = BaiduStructureZipperService(
            access_token=self.access_token,
            user_id=user_id,
            temp_dir=temp_dir
        )
        result = structure_service.incremental_update_structure_data(user_id, account_id)
        logger.info_service(f"增量更新百度广告账户{user_id}的结构数据结束，结果: {result.message}")
        return result
    def notify_result(self):
        pass
    def run(self):
        self.oauth().get_ads_report_data()


