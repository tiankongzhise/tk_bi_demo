from ..config import get_config_settings
from ..utils import accept_both_cases

from tk_base_utils.tk_http import ClientConfig,HttpClient
from tk_base_utils.tk_http.exceptions import HttpClientError


def _load_http_config(headers:dict|None=None,user_agent:str|None=None):
    """加载HTTP配置"""
    config_settings = get_config_settings()
    http_config = config_settings.http_config
    
    http_config['headers'] =headers or {
        "Content-Type": "application/json;charset:utf-8;",
    }
    http_config['user_agent'] = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
    return ClientConfig(**http_config)

class BaiduHttpClient(object):
    def __init__(self, headers: dict | None = None, user_agent: str | None = None) -> None:
        self.client = HttpClient(_load_http_config(headers, user_agent))
    
    def set_oauth_account(self,user_name:str,access_token:str|None = None):
        if access_token:
            self.access_token = access_token
        if not hasattr(self,'access_token'):
            raise HttpClientError(message='未oauth鉴权,请先完成oauth认证',status_code=401)
        self.user_name = user_name

    @property
    def _query_headers(self):
        return {
            "userName":self.user_name,
            "accessToken":self.access_token,
        }
    
    
    
    def refresh_token(self,app_id:str,refresh_token,secret_key:str,user_id:int|str):
        """更新授权令牌接口"""
        url = 'https://u.baidu.com/oauth/refreshToken'
        json_params ={
            "appId": app_id,
            "refreshToken": refresh_token,
            "secretKey": secret_key,
            "userId": int(user_id),
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    @accept_both_cases('report_type','time_unit','start_date','end_date','columns')
    def create_report_task(self,
                           report_type:str|int|None = None,
                           time_unit:str|None = None,
                           start_date:str|None = None,
                           end_date:str|None = None,
                           columns:list[str]|None = None,
                           **kwargs
                           ):
        """创建异步任务"""
        url = 'https://api.baidu.com/json/sms/service/OpenApiReportService/createReportTask'
        json_params = {
            "header":self._query_headers,
            "body":{
                "reportType":int(report_type),
                "timeUnit":time_unit,
                "startDate":start_date,
                "endDate":end_date,
                "columns":columns,
                **kwargs
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()



