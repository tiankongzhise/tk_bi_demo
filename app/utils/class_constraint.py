from abc import ABC, abstractmethod

class AdsDataCaptureFactory(ABC):
    @abstractmethod
    def oauth(self):
        ...
    @abstractmethod
    def get_ads_report_data(self):  
        ...
    @abstractmethod
    def get_ads_account_structure(self):
        ...
    @abstractmethod
    def update_ads_data(self):
        ...
    @abstractmethod
    def update_ads_account_structure(self):
        ...
    # 将更新结果通知给前端
    @abstractmethod
    def notify_result(self):
        ...
    @abstractmethod
    def run(self):
        ...
