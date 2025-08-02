from abc import ABC, abstractmethod
from ..models import AdsQueryParams,BdAdsQueryParams







class UpdateAdsDataFactory(ABC):
    @abstractmethod
    def __init__(self,channel:str,ads_query_params:AdsQueryParams):
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
    def __init__(self,channel:str,ads_query_params:BdAdsQueryParams):
        super().__init__(channel,ads_query_params)
    def oauth(self):
        pass
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
