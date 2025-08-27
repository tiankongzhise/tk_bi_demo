from sqlalchemy.orm import query
from ..logger import create_logger,logger_wrapper
from ..config import get_config_settings
from ..kernel import BaiduHttpClient
from ..utils import camel_to_snake
from ..database import insert_baidu_keyword_daily,insert_baidu_keyword_hour
from ..models.base import ReturnModel

from tk_base_utils.tk_http.exceptions import TimeoutError,HttpClientError
from pathlib import Path
from typing import Generator

import time
from datetime import datetime
logger = create_logger(__name__)

class Utils(object):
    @staticmethod
    def _is_time_valid(time_str:str):
        try:
            datetime.strptime(time_str, "%Y-%m-%d")
            return True
        except ValueError:
            pass
        try:
            datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            pass
        return False
    @staticmethod
    # 验证get_changed_scale的start_time入参是否合规,要求为满足%Y-%m-%d或者%Y-%m-%d HH:MM:SS 且时间以现在为起点不能早于上个月的1月1日
    def filed_valid_start_time(start_time:str|None = None):
        if start_time is None:
            raise ValueError("get_changed_scale的start_time为空,出现意料之外的错误")
        if not Utils._is_time_valid(start_time):
            raise ValueError("get_changed_scale的start_time格式错误,要求为%Y-%m-%d或者%Y-%m-%d HH:MM:SS")
        try:
            start_time_local = datetime.strptime(start_time, "%Y-%m-%d")
        except ValueError:
            start_time_local = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        # 验证start_time是否早于上个月的1月1日 00:00:00 只比较到秒
        if start_time_local < datetime.now().replace(day=1, month=datetime.now().month-1, hour=0, minute=0, second=0, microsecond=0):
            raise ValueError("get_changed_scale的start_time不能早于上个月的1月1日 00:00:00:00")
        return True

    @staticmethod
    def get_last_month_time():
        """获取上个月的时间"""
        last_month = datetime.now().month - 1
        last_year = datetime.now().year
        if last_month == 0:
            last_month = 12
            last_year -= 1
        return f"{last_year}-{last_month}-01"

class FetchStructureBaiduCore:
    def __init__(self,access_token:str,user_name:str,temp_dir:str) -> None:
        self.config_settings = get_config_settings()
        self.http_client = BaiduHttpClient()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
        self._changed_count = None
        self._start_time = None
        self._max_changed_count = 20000
        self._search_level_list = ['campaign','adgroup','keyword','creative','autoExpansion']
        self._feed_level_list = ['campaignFeed','adgroupFeed','creativeFeed','atpFeed']
        self._max_wait_time = 60
        self._max_re_cancel_count = 3
    
    def reset_core(self,access_token:str,user_name:str,temp_dir:str):
        self.config_settings = get_config_settings()
        self.http_client.set_oauth_account(user_name,access_token)
        self.user_name = user_name
        self.temp_dir:str|Path = temp_dir
        self._changed_count = None
        self._start_time = None
        self._max_changed_count = 20000
        
    def get_changed_scale(self):
        """获取变更规模"""
        if self._start_time is None:
            self._start_time = Utils.get_last_month_time()
        if not Utils.filed_valid_start_time(self._start_time):
            raise ValueError(f"get_changed_scale的start_time格式错误,要求为%Y-%m-%d或者%Y-%m-%d HH:MM:SS,当前为{self._start_time}")
        rsp = self.http_client.get_changed_scale(self._start_time)
        changed_data:dict[str,list] = rsp.get('body',{}).get('data',[{}])[0]
        changed_count = 0
        for key,value in changed_data.items():
            if 'Scale' in key:
                changed_count += value[0]
        return changed_count
            
    
    def get_changed_objects(self,query_params:dict|None = None):
        """增量下载"""
        if query_params is None:
            query_params = {
                'mobileExtend':1
            }
            query_params.update({
                f'{level}Fields':['all'] for level in self._search_level_list
            })
            query_params['businessLabelFields'] = ['all']
        
        if self._start_time is None:
            self._start_time = Utils.get_last_month_time()
        try:
            rsp = self.http_client.get_all_changed_objects(self._start_time,**query_params)
            if rsp.get('body',{}).get('data',[{}])[0].get('fileId'):
                logger.info_core(f"{self.user_name}增量下载成功,响应数据: {rsp}")
                return ReturnModel(status='success',
                                   message=f'百度渠道,账户:{self.user_name},账户变化增量任务创建成功',
                                   data=rsp.get('body',{}).get('data',[{}])[0].get('fileId'))
            else:
                logger.info_core(f"{self.user_name}增量下载返回异常,响应数据: {rsp}")
                return ReturnModel(status='error',
                                   message=f'百度渠道,账户:{self.user_name},账户变化增量任务创建异常,响应数据: {rsp}',
                                   data=None)
        except Exception as e:
            logger.error(f"{self.user_name}增量下载失败,异常信息: {e}")
            return ReturnModel(status='error',
                               message=f'百度渠道,账户:{self.user_name},账户变化增量任务创建异常,异常信息: {e}',
                               data=None)
    
    def get_all_objects(self):
        """全量下载"""
        pass
    
    def get_objects_status(self,file_id:str):
        """查询文件状态"""
        wait_time = 0
        while True:
            rsp = self.http_client.get_file_status(file_id)
            file_status = rsp.get('body',{}).get('data',[{}])[0].get('isGenerated')
            if file_status == 3:
                return ReturnModel(status='success',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},状态查询成功,文件已生成',
                                data=file_id)
            elif file_status == 5:
                self.cancel_download(file_id)
                return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},部分成功,响应数据: {rsp}',
                                data=None)
            else:
                logger.info_core(f"百度渠道,账户:{self.user_name},文件ID:{file_id},状态查询生产中,响应数据: {rsp},延迟5秒再查询")
                time.sleep(5)
                wait_time += 5
                if wait_time > self._max_wait_time:
                    self.cancel_download(file_id)
                    return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},状态查询超时,响应数据: {rsp}',
                                data=None)
    
    def get_objects_file_path(self,file_id:str):
        """获取文件下载地址"""
        try:
            rsp = self.http_client.get_file_path(file_id)
            file_path = rsp.get('body',{}).get('data',[{}])[0]
            if file_path:
                return ReturnModel(status='success',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},获取文件下载地址成功,响应数据: {rsp}',
                                data=file_path)
            else:
                return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},获取文件下载地址失败,响应数据: {rsp}',
                                data=None)
        except Exception as e:
            logger.error(f"获取文件下载地址失败,异常信息: {e}")
            return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},获取文件下载地址失败,异常信息: {e}',
                                data=None)
    
    def download_objects(self, file_path_dict: dict, max_workers: int = 3) -> dict:
        """批量下载文件
        
        Args:
            file_path_dict: 文件路径字典，格式为 {file_id: {'url': str, 'md5': str}}
            max_workers: 最大并发下载数，默认3个
            
        Returns:
            dict: 下载结果字典
                {
                    'success_count': int,  # 成功下载的文件数
                    'failed_count': int,   # 失败下载的文件数
                    'total_count': int,    # 总文件数
                    'results': dict,       # 详细结果 {file_id: download_result}
                    'success_files': list, # 成功下载的文件路径列表
                    'failed_files': list   # 失败下载的文件信息列表
                }
        """
        import concurrent.futures
        import threading
        
        if not file_path_dict:
            logger.info_core(f"百度渠道,账户:{self.user_name},没有文件需要下载")
            return {
                'success_count': 0,
                'failed_count': 0,
                'total_count': 0,
                'results': {},
                'success_files': [],
                'failed_files': []
            }
        
        total_count = len(file_path_dict)
        results = {}
        success_files = []
        failed_files = []
        
        # 线程锁，用于保护共享资源
        lock = threading.Lock()
        
        def download_single_file(file_id, file_info):
            """下载单个文件的内部函数"""
            try:
                file_url = file_info.get('url')
                expected_md5 = file_info.get('md5')
                
                if not file_url:
                    return file_id, {
                        'success': False,
                        'error': '文件URL为空',
                        'file_id': file_id
                    }
                
                # 生成包含文件ID的文件名
                custom_filename = f"{self.user_name}_baidu_{file_id}.txt"
                
                result = self.download_object(
                    file_url=file_url,
                    expected_md5=expected_md5,
                    custom_filename=custom_filename
                )
                
                result['file_id'] = file_id
                return file_id, result
                
            except Exception as e:
                error_msg = f"下载文件{file_id}时发生异常: {str(e)}"
                logger.error(f"百度渠道,账户:{self.user_name},{error_msg}")
                return file_id, {
                    'success': False,
                    'error': error_msg,
                    'file_id': file_id
                }
        
        logger.info_core(f"百度渠道,账户:{self.user_name},开始批量下载{total_count}个文件,并发数:{max_workers}")
        
        # 使用线程池进行并发下载
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            future_to_file = {
                executor.submit(download_single_file, file_id, file_info): file_id
                for file_id, file_info in file_path_dict.items()
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_file):
                file_id = future_to_file[future]
                try:
                    result_file_id, result = future.result()
                    
                    with lock:
                        results[result_file_id] = result
                        
                        if result['success']:
                            success_files.append(result['file_path'])
                            logger.info_core(f"百度渠道,账户:{self.user_name},文件{result_file_id}下载成功")
                        else:
                            failed_files.append({
                                'file_id': result_file_id,
                                'error': result.get('error', '未知错误')
                            })
                            logger.error(f"百度渠道,账户:{self.user_name},文件{result_file_id}下载失败: {result.get('error')}")
                            
                except Exception as e:
                    error_msg = f"处理文件{file_id}结果时发生异常: {str(e)}"
                    logger.error(f"百度渠道,账户:{self.user_name},{error_msg}")
                    
                    with lock:
                        results[file_id] = {
                            'success': False,
                            'error': error_msg,
                            'file_id': file_id
                        }
                        failed_files.append({
                            'file_id': file_id,
                            'error': error_msg
                        })
        
        success_count = len(success_files)
        failed_count = len(failed_files)
        
        logger.info_core(f"百度渠道,账户:{self.user_name},批量下载完成: 成功{success_count}个, 失败{failed_count}个, 总计{total_count}个")
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': total_count,
            'results': results,
            'success_files': success_files,
            'failed_files': failed_files
        }
    
    def download_object(self, file_url: str, expected_md5: str = None, custom_filename: str = None) -> dict:
        """下载单个文件到临时目录
        
        Args:
            file_url: 文件下载URL
            expected_md5: 期望的MD5值，用于校验文件完整性
            custom_filename: 自定义文件名，如果不提供则从URL中提取或生成
            
        Returns:
            dict: 包含下载结果的字典
                {
                    'success': bool,  # 下载是否成功
                    'file_path': str,  # 下载文件的完整路径
                    'file_name': str,  # 文件名
                    'md5': str,  # 文件的MD5值
                    'error': str,  # 错误信息（如果有）
                    'account': str  # 账户名
                }
        """
        import os
        from urllib.parse import urlparse, unquote
        
        # 确保临时目录存在
        temp_dir = Path(self.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 计算文件名
        if custom_filename:
            file_name = custom_filename
        else:
            # 从URL中提取文件名
            parsed_url = urlparse(file_url)
            file_name = unquote(parsed_url.path.split('/')[-1])
            if not file_name or file_name == '/':
                # 如果无法从URL提取文件名，使用账户名和时间戳生成
                import time
                timestamp = int(time.time())
                file_name = f"{self.user_name}_baidu_structure_{timestamp}.txt"
        
        # 确保文件名包含账户信息（如果还没有的话）
        if self.user_name not in file_name:
            name_parts = file_name.rsplit('.', 1)
            if len(name_parts) == 2:
                file_name = f"{name_parts[0]}_{self.user_name}.{name_parts[1]}"
            else:
                file_name = f"{file_name}_{self.user_name}"
        
        logger.info_core(f"百度渠道,账户:{self.user_name},开始下载文件: {file_url}")
        
        try:
            # 调用BaiduHttpClient的download_object方法
            result = self.http_client.download_object(
                file_url=file_url,
                download_dir=temp_dir,
                expected_md5=expected_md5
            )
            
            # 如果下载成功但文件名不符合预期，重命名文件
            if result['success'] and result['file_name'] != file_name:
                old_path = Path(result['file_path'])
                new_path = temp_dir / file_name
                
                # 如果目标文件已存在，添加序号
                counter = 1
                original_name = file_name
                while new_path.exists():
                    name_parts = original_name.rsplit('.', 1)
                    if len(name_parts) == 2:
                        file_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        file_name = f"{original_name}_{counter}"
                    new_path = temp_dir / file_name
                    counter += 1
                
                # 重命名文件
                old_path.rename(new_path)
                result['file_path'] = str(new_path)
                result['file_name'] = file_name
            
            # 添加账户信息到结果中
            result['account'] = self.user_name
            
            if result['success']:
                logger.info_core(f"百度渠道,账户:{self.user_name},文件下载成功: {result['file_path']}, MD5: {result['md5']}")
            else:
                logger.error(f"百度渠道,账户:{self.user_name},文件下载失败: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"下载文件时发生异常: {str(e)}"
            logger.error(f"百度渠道,账户:{self.user_name},{error_msg}")
            return {
                'success': False,
                'file_path': str(temp_dir / file_name),
                'file_name': file_name,
                'md5': None,
                'error': error_msg,
                'account': self.user_name
            }
    
    def cancel_download(self,file_id:str):
        """取消下载"""
        re_cancel_time = 0
        while True:
            rsp = self.http_client.cancel_download(file_id)
            if rsp.get('body',{}).get('data',[{}])[0].get('isCancelled') == 3:
                return ReturnModel(status='success',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},取消下载成功,响应数据: {rsp}',
                                data=file_id)
            else:
                logger.info_core(f"百度渠道,账户:{self.user_name},文件ID:{file_id},取消下载失败,响应数据: {rsp},延迟5秒再取消,目前已重试{re_cancel_time}次")
                time.sleep(5)
                re_cancel_time += 1
                if re_cancel_time > self._max_re_cancel_count:
                    return ReturnModel(status='error',
                                message=f'百度渠道,账户:{self.user_name},文件ID:{file_id},取消下载失败,响应数据: {rsp}',
                                data=file_id)
    

    
    def choose_get_objects_function(self):
        """选择全量下载还是增量下载"""
        changed_count = self.get_changed_scale(self._start_time)
        if changed_count > self._max_changed_count:
            logger.info_core(f"变更数据量{changed_count}大于{self._max_changed_count},选择全量下载")
            return self.get_all_objects
        else:
            logger.info_core(f"变更数据量{changed_count}小于{self._max_changed_count},选择增量下载")
            return self.get_changed_objects
        
    
    def create_objects_task(self):
        """创建下载任务"""
        pass


    def run(self):
        """运行"""
        self.get_changed_scale()
        self.choose_get_objects_function()
        self.create_objects_task()
        self.get_objects_status()
        self.get_objects_file_path()
        self.download_objects()

