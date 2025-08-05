from abc import ABC, abstractmethod
from typing import Type,TypeVar
from ..models import AdsQueryParams,BdAdsQueryParams
from ..core.update_ads_data.baidu import BaiduOauthCore


T = TypeVar('T',bound=AdsQueryParams)



class UpdateAdsDataFactory(ABC):
    @abstractmethod
    def __init__(self,channel:str,ads_query_params:Type[T]):
        self.channel = channel
        self.ads_query_params = ads_query_params
    @abstractmethod
    def oauth(self):
        pass
    @abstractmethod
    def get_ads_report_data(self):  
        pass
    @abstractmethod
    def get_ads_account_structure(self):
        pass
    @abstractmethod
    def update_ads_data(self):
        pass
    @abstractmethod
    def update_ads_account_structure(self):
        pass
    # 检查账户结构与报告数据的计划单元名称是否一致
    @abstractmethod
    def check_account_structure_with_report_data(self):
        pass
    # 将更新结果通知给前端
    @abstractmethod
    def notify_update_result(self):
        pass


class UpdateBdAdsData(UpdateAdsDataFactory):
    def __init__(self,ads_query_params:BdAdsQueryParams):
        super().__init__("baidu",ads_query_params)
    def oauth(self):
        oauth_service = BaiduOauthCore(controler_id=self.ads_query_params.controler_id,
                                     controler_name=self.ads_query_params.controler_name)
        oauth_info = oauth_service.oauth()
        self.access_token = oauth_info.access_token
    def get_ads_report_data(self):
        pass
    def get_ads_account_structure(self):
        pass
    def update_ads_data(self):
        pass
    def update_ads_account_structure(self):
        pass
    def check_account_structure_with_report_data(self):
        pass
