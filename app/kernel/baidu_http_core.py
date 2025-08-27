from ..config import get_config_settings
from ..utils import accept_both_cases

from tk_base_utils.tk_http import ClientConfig,HttpClient
from tk_base_utils.tk_http.exceptions import HttpClientError
from pathlib import Path



def _load_http_config(headers:dict|None=None,user_agent:str|None=None):
    """加载HTTP配置"""
    config_settings = get_config_settings()
    http_config = config_settings.http_config
    
    http_config['headers'] ={ "Content-Type": "application/json;charset:utf-8;"} if headers is None else headers
    http_config['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0' if user_agent is None else user_agent

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
    
    @property
    def _get_headers(self):
        return {
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
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

    @accept_both_cases('task_id')
    def get_report_task_status(self,
                               task_id:str|int):
        """获取异步任务状态"""
        url = 'https://api.baidu.com/json/sms/service/OpenApiReportService/getTaskStatus'
        json_params = {
            "header":self._query_headers,
            "body":{
                "taskId":str(task_id),
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()


    @accept_both_cases('file_url', 'table_header', 'data_start_row', 'file_path')
    def download_file(self, file_url: str, table_header: list[str], data_start_row: int, file_path: str|Path) -> Path:
        """下载文件到指定位置,file_url为文件的下载链接,
        table_header为文件的表头列名,需要保序,并根据传入的table_header写入表头
        data_start_row指定数据起始行,数据在文件中的起始行。文件的前几行为表头或其他信息,data_start_row为数据的起始行,
        保存为制表符分隔的文本文件(.txt)
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # http_config = _load_http_config({})
        # download_client = HttpClient(http_config)
        # with download_client as client:
        #     rsp = client.get(file_url)
        # #     content_text = rsp.text
        with self.client as client:
            rsp = client.get(file_url,default_headers=False)

            if rsp.raise_for_status():
                return False

            # 尝试不同编码解码响应内容
            code_list = ['gb18030','utf-8','big5']

            content_text = None
            for code in code_list:
                try:
                    content_text = rsp.content.decode(code)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content_text is None:
                raise HttpClientError(message='所有编码尝试失败')




        
        # 解析制表符分隔的内容
        lines = content_text.splitlines()

        
        # 提取数据行（从指定行开始）
        if data_start_row <= len(lines):
            data_lines = lines[data_start_row - 1:]  # 转换为0索引

        else:
            # 如果数据起始行超出文件行数，返回空数据
            data_lines = []
        
        # 写入新的制表符分隔文件
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            # 写入自定义表头
            if table_header:
                header_line = '\t'.join(table_header)
                f.write(header_line + '\n')

            
            # 写入数据行（保持原始制表符分隔格式）
            for line in data_lines:
                f.write(line + '\n')
        return file_path


    @accept_both_cases('start_time')
    def get_changed_scale(self,start_time:str,campaign_ids:list[int]|None = None,**kwargs):
        """获取变更规模
        获取完整账户下，或者指定计划ID下的变化物料规模，从而帮助用户决定后续的最近更新策略。当有变化的物料规模大于一定比例时，用户不妨选择整账户下载
        注：变化物料仅指因用户操作发生的变化，即在历史操作记录中可以查询到的操作。而对于质量度，状态这些在系统内自动发生的改变不在统计范围内
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/getChangedScale'
        if campaign_ids is None:
            campaign_ids = []
        json_params = {
            "header":self._query_headers,
            "body":{
                "startTime":start_time,
                "campaignIds":campaign_ids,
                **kwargs
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    @accept_both_cases('start_time','item_type')
    def get_changed_item_id(self,start_time:str,
                            item_type:int,
                            ids:list[int]|None = None,
                            **kwargs):
        """
        获取有变化物料id
        获取从指定时间到当前时间段内有变化的物料id。默认返回数据限制不超过两万条。 超过数量限制的物料id，可使用分页参数请求获得。
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/getChangedItemId'
        json_params = {
            "header":self._query_headers,
            "body":{
                "startTime":start_time,
                "itemType":item_type,
                "ids":ids or [],
                **kwargs
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    @accept_both_cases('start_time')
    def get_all_changed_objects(self,start_time:str,
                                campaign_ids:list[int]|None=None,
                                mobile_extend:int=0,
                                include_temp:bool=True,
                                **kwargs):
        """增量下载
        方法说明
        通过该接口获取完整账户下，或者指定计划ID下的有变化的物料信息。该接口为异步接口，返回请求的结果文件ID。定制需要返回的层级文件，以及各层级文件中的数据列
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/getAllChangedObjects'
        json_params = {
            "header":self._query_headers,
            "body":{
                "startTime":start_time,
                "campaignIds":campaign_ids or [],
                "mobileExtend":mobile_extend,
                "includeTemp":include_temp,
                **kwargs
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    def get_file_status(self,file_id:str):
        """查询文件状态
        方法说明
        在调用getAllObejects、getAllChangedObjects接口后使用，以查询请求的文件是否已生成。
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/getFileStatus'
        json_params = {
            "header":self._query_headers,
            "body":{
                "fileId":file_id,
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    def get_file_path(self,file_id:str):
        """获取文件下载地址
        方法说明
        返回请求的文件下载地址。使用接口：getAllObjects，getAllChangedObjects。按照请求的下载文件顺序返回。
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/getFilePath'
        json_params = {
            "header":self._query_headers,
            "body":{
                "fileId":file_id,
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    def get_all_objects(self,campaign_ids:list[int]|None=None,**kwargs):
        """整账户下载
        方法说明
        获取指定账户下的完整数据（计划、单元、关键词、创意、素材）
        获取指定计划下的完整数据（计划、单元、关键词、创意、素材）
        定制需要返回的层级文件，以及各层级文件中的数据列
        关键词层级新增关键词指导价1个字段（计算机指导价、移动指导价），本次新增内容非基本字段，通过all无法直接获取；如需获取参考如下：举例：如需获取计算机指导价，可通过新增请求字段方式获取keywordFields ["all","leftPriceGuide"]
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/getAllObjects'
        json_params = {
            "header":self._query_headers,
            "body":{
                "campaignIds":campaign_ids or [],
                **kwargs
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    def cancel_download(self,file_id:str):
        """取消下载
        方法说明
        取消指定文件的下载任务。
        """
        url = 'https://api.baidu.com/json/sms/service/BulkJobService/cancelDownload'
        json_params = {
            "header":self._query_headers,
            "body":{
                "fileId":file_id,
            }
        }
        with self.client as client:
            rsp = client.post(url,json=json_params)
        return rsp.json()

    def download_object(self,file_url:str,download_dir:str|Path):
        """下载文件"""
        ...

