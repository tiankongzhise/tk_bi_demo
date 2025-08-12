from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from .baidu_http_core import BaiduHttpClient
from ..utils import camel_to_snake
from ..database import insert_baidu_keyword_daily,insert_baidu_keyword_hour

from tk_base_utils.tk_http.exceptions import TimeoutError,HttpClientError
from pathlib import Path
from typing import Generator

import time
from datetime import datetime
logger = create_logger(__name__)




class FetchAdsDataBaiduCore:
    """
    百度广告数据获取核心类
    """
    @logger_wrapper()
    def __init__(self,access_token:str,user_name:str,temp_dir:str|Path) -> None:

        self.config_settings = get_config_settings()
        self.http_client = BaiduHttpClient()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
        self.report_name:str = None

    @logger_wrapper()
    def create_report_task(self,report_name:str):
        self.report_name = report_name
        report_params = self.config_settings.get_baidu_report_config(report_name)
        response = self.http_client.create_report_task(**report_params)
        logger.info(f"{self.user_name}创建报告任务响应: {response}")
        if response.get('header',{}).get('desc','') == 'success':
            try:
                task_id = response['body']['data'][0]['taskId']
                self.task_id = task_id
            except (KeyError,IndexError) as e:
                logger.error(f"{self.user_name}创建报告任务失败,响应数据异常: {e},response:{response}")
                raise HttpClientError(f"{self.user_name}创建报告任务失败,响应数据异常: {e},response:{response}")

            logger.info(f"{self.user_name}创建报告任务成功,任务ID: {task_id}")
            return task_id
        else:
            logger.error(f"{self.user_name}创建报告任务失败,响应数据异常: {response}")
            raise HttpClientError(f"{self.user_name}创建报告任务失败,响应数据异常: {response}")

    def get_task_status(self,task_id:str|int):
        response = self.http_client.get_report_task_status(task_id)
        logger.info(f"{self.user_name}获取报告任务状态响应: {response}")
        return response
    def fetch_report_data(self,task_id:str|int):
        time_cost = 0
        while True:
            response = self.get_task_status(task_id)
            status = response.get('body',{}).get('data',[{}])[0].get('taskStatus','')
            if status == 'SUCCESS':
                logger.info(f"{self.user_name}获取报告任务数据成功,任务ID: {task_id},响应数据: {response}")
                break
            elif status == 'FAIL':
                logger.error(f"{self.user_name}获取报告任务数据失败,任务ID: {task_id},响应数据: {response}")
                raise HttpClientError(f"{self.user_name}获取报告任务数据失败,任务ID: {task_id},响应数据: {response}")
            else:
                time.sleep(1)
                time_cost += 1
                if time_cost > 60:
                    logger.error(f"{self.user_name}获取报告任务数据超时,任务ID: {task_id},响应数据: {response}")
                    raise TimeoutError
        
        try:
            file_url = response['body']['data'][0]['fileUrl']
            data_start_row = response['body']['data'][0]['dataStartRow']
            table_header = response['body']['data'][0]['tableHeader']
        except (KeyError,IndexError) as e:
            logger.error(f"{self.user_name}获取报告任务数据意料之外的错误,任务ID: {task_id},响应数据: {response},错误信息: {e}")
            raise HttpClientError(f"{self.user_name}获取报告任务数据意料之外的错误,任务ID: {task_id},响应数据: {response},错误信息: {e}")
        self.file_path = Path(self.temp_dir)/f"{self.user_name}_{self.report_name}_{task_id}.txt"
        self.file_path.parent.mkdir(parents=True,exist_ok=True)
        try:
            temp_file_path = self.http_client.download_file(file_url,table_header,data_start_row,self.file_path)
            logger.info(f"{self.user_name}下载报告任务数据成功,任务ID: {task_id},文件路径: {temp_file_path}")
            return temp_file_path
        except HttpClientError as e:
            logger.error(f"{self.user_name}下载报告任务数据失败,任务ID: {task_id},响应数据: {response},错误信息: {e}")
            raise HttpClientError(f"{self.user_name}下载报告任务数据失败,任务ID: {task_id},响应数据: {response},错误信息: {e}")
    def process_report_data(self,file_path:Path):
        if 'keyword_day' in self.report_name:
            return self._process_baidu_keyword_daily(file_path)
        if 'keyword_hour' in self.report_name:
            return self._process_baidu_keyword_hour(file_path)

        logger.error(f"类型转化出错,{self.user_name}不支持的报告类型: {self.report_name}")
        raise HttpClientError(f"{self.user_name}不支持的报告类型: {self.report_name}")

    def save_report_data(self,data_generator:Generator[tuple,None,None]):
        if 'keyword_day' in self.report_name:
            insert_result = insert_baidu_keyword_daily(data_generator)
            logger.info(f"{self.user_name}保存报告数据完成,报告类型: {self.report_name},插入结果: {insert_result}")
            return insert_result
        elif 'keyword_hour' in self.report_name:
            insert_result = insert_baidu_keyword_hour(data_generator)
            logger.info(f"{self.user_name}保存报告数据完成,报告类型: {self.report_name},插入结果: {insert_result}")
            return insert_result





        logger.error(f"数据存储出错{self.user_name}不支持的报告类型: {self.report_name}")
        raise HttpClientError(f"{self.user_name}不支持的报告类型: {self.report_name}")



    def run(self,report_name:str):
        task_id = self.create_report_task(report_name)
        temp_file_path = self.fetch_report_data(task_id)
        data_generator = self.process_report_data(temp_file_path)
        self.save_report_data(data_generator)
    


    def _process_baidu_keyword_daily(self,file_path:Path):
        """生成器函数，从文件读取数据
        第一行是表头，直接返回
        后续每次yield一行数据，以tuple形式，每行内部以\t分割数据
        """
        header_line = None
        table_colums = ['report_date','user_name','campaign_id','w_info_id']
        
        with open(file_path,'r',encoding='utf-8') as f:
             # 逐行读取数据并yield
             for line in f:
                 line = line.strip()
                 if line:  # 跳过空行
                    # 以制表符分割数据，返回tuple
                    temp_data =  tuple(line.split('\t'))
                    if header_line is None:
                        header_line = temp_data
                        header_line = [camel_to_snake(header) for header in header_line]
                        continue  # 跳过表头行，不处理为数据
                    
                    data_dict = dict(zip(header_line,temp_data))
                    date_str = data_dict.pop('date')
                    date_datetime = datetime.strptime(date_str,'%Y-%m-%d')
                    data_dict['report_date'] = date_datetime
                    temp_dict = {'data_json':{}}
                    for key,value in data_dict.items():
                        if key in table_colums:
                            # 将campaign_id和w_info_id转换为整数
                            if key in ['campaign_id', 'w_info_id']:
                                temp_dict[key] = int(value)
                            else:
                                temp_dict[key] = value
                        else:
                            temp_dict['data_json'][key] = value
                    yield temp_dict



    def _process_baidu_keyword_hour(self,file_path:Path):
        """生成器函数，从文件读取数据
        第一行是表头，直接返回
        后续每次yield一行数据，以tuple形式，每行内部以\t分割数据
        """
        header_line = None
        table_colums = ['report_date','hour','user_name','campaign_id','w_info_id']
        with open(file_path,'r',encoding='utf-8') as f:
             # 逐行读取数据并yield
             for line in f:
                 line = line.strip()
                 if line:  # 跳过空行
                    # 以制表符分割数据，返回tuple
                    temp_data =  tuple(line.split('\t'))
                    if header_line is None:
                        header_line = temp_data
                        header_line = [camel_to_snake(header) for header in header_line]
                        continue  # 跳过表头行，不处理为数据
                    
                    data_dict = dict(zip(header_line,temp_data))
                    date_str = data_dict.pop('date')
                    date_datetime = datetime.strptime(date_str,'%Y-%m-%d')
                    data_dict['report_date'] = date_datetime
                    temp_dict = {'data_json':{}}
                    for key,value in data_dict.items():
                        if key in table_colums:
                            # 将campaign_id和w_info_id转换为整数
                            if key in ['campaign_id', 'w_info_id']:
                                temp_dict[key] = int(value)
                            else:
                                temp_dict[key] = value
                        else:
                            temp_dict['data_json'][key] = value
                    yield temp_dict


