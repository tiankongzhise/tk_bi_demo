from ..logger import create_logger, logger_wrapper
from ..config import get_config_settings
from ..core import FetchStructureBaiduCore
from ..database.zipper_operations import (
    campaign_zipper_ops,
    adgroup_zipper_ops,
    keyword_zipper_ops,
    creative_zipper_ops
)
from ..models.base import ReturnModel
from ..utils import camel_to_snake

from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import zipfile
import csv
from datetime import datetime

logger = create_logger(__name__)


class BaiduStructureZipperService:
    """百度广告结构数据拉链表服务"""
    
    @logger_wrapper(level="INFO_SERVICE")
    def __init__(self, access_token: str, user_id: str, temp_dir: str):
        self.access_token = access_token
        self.user_id = user_id
        self.temp_dir = Path(temp_dir)
        self.config_settings = get_config_settings()
        
        # 初始化结构数据获取核心
        self.fetch_core = FetchStructureBaiduCore(
            access_token=access_token,
            user_name=user_id,
            temp_dir=str(temp_dir)
        )
    
    def _parse_structure_file(self, file_path: Path, data_type: str) -> List[Dict[str, Any]]:
        """解析结构数据文件"""
        parsed_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 假设是TSV格式
                reader = csv.DictReader(f, delimiter='\t')
                
                for row in reader:
                    # 转换字段名为snake_case
                    converted_row = {}
                    for key, value in row.items():
                        snake_key = camel_to_snake(key)
                        converted_row[snake_key] = value
                    
                    # 添加用户ID
                    converted_row['user_id'] = self.user_id
                    
                    # 根据数据类型进行特殊处理
                    if data_type == 'keyword' or data_type == 'autoExpansion':
                        # 确保关键词ID字段存在
                        if 'keyword_id' not in converted_row and 'w_info_id' in converted_row:
                            converted_row['keyword_id'] = converted_row['w_info_id']
                    
                    parsed_data.append(converted_row)
                    
        except Exception as e:
            logger.error(f"解析{data_type}文件失败: {file_path}, 错误: {e}")
            raise
        
        logger.info_service(f"解析{data_type}文件完成: {file_path}, 共{len(parsed_data)}条记录")
        return parsed_data
    
    def _extract_and_parse_structure_files(self, file_path_dict: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """提取并解析结构数据文件"""
        structure_data = {
            'campaign': [],
            'adgroup': [],
            'keyword': [],
            'creative': [],
            'autoExpansion': []
        }
        
        for data_type, zip_file_path in file_path_dict.items():
            if data_type not in structure_data:
                continue
                
            try:
                # 解压文件
                extract_dir = self.temp_dir / f"extract_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # 查找数据文件（通常是.txt或.csv文件）
                data_files = list(extract_dir.glob('*.txt')) + list(extract_dir.glob('*.csv'))
                
                if data_files:
                    data_file = data_files[0]  # 取第一个文件
                    structure_data[data_type] = self._parse_structure_file(data_file, data_type)
                else:
                    logger.warning(f"在{extract_dir}中未找到数据文件")
                    
            except Exception as e:
                logger.error(f"处理{data_type}文件失败: {zip_file_path}, 错误: {e}")
                continue
        
        return structure_data
    
    @logger_wrapper(level="INFO_SERVICE")
    def full_update_structure_data(self) -> ReturnModel:
        """全量更新结构数据"""
        try:
            logger.info_service(f"开始全量更新百度账户{self.user_id}的结构数据")
            
            # 1. 获取全量数据
            result = self.fetch_core.get_all_objects()
            if result.status != 'success':
                return result
            
            file_id = result.data
            
            # 2. 等待文件准备完成
            status_result = self.fetch_core.get_objects_status(file_id)
            if status_result.status != 'success':
                return status_result
            
            # 3. 获取文件下载路径
            file_path_result = self.fetch_core.get_objects_file_path(file_id)
            if file_path_result.status != 'success':
                return file_path_result
            
            file_path_dict = file_path_result.data
            
            # 4. 下载文件
            download_result = self.fetch_core.download_objects(file_path_dict)
            if not download_result.get('success', False):
                return ReturnModel(
                    status='error',
                    message=f'文件下载失败: {download_result.get("message")}',
                    data=None
                )
            
            # 5. 解析文件数据
            structure_data = self._extract_and_parse_structure_files(download_result['file_paths'])
            
            # 6. 更新拉链表数据
            self._update_zipper_tables(structure_data, is_full_update=True)
            
            logger.info_service(f"百度账户{self.user_id}全量更新完成")
            return ReturnModel(
                status='success',
                message=f'百度账户{self.user_id}全量更新成功',
                data={
                    'campaign_count': len(structure_data['campaign']),
                    'adgroup_count': len(structure_data['adgroup']),
                    'keyword_count': len(structure_data['keyword']),
                    'creative_count': len(structure_data['creative']),
                    'auto_expansion_count': len(structure_data['autoExpansion'])
                }
            )
            
        except Exception as e:
            logger.error(f"全量更新失败: {e}")
            return ReturnModel(
                status='error',
                message=f'全量更新失败: {str(e)}',
                data=None
            )
    
    @logger_wrapper(level="INFO_SERVICE")
    def incremental_update_structure_data(self, start_time: Optional[str] = None) -> ReturnModel:
        """增量更新结构数据"""
        try:
            logger.info_service(f"开始增量更新百度账户{self.user_id}的结构数据")
            
            # 设置开始时间
            if start_time:
                self.fetch_core._start_time = start_time
            
            # 1. 检查变更规模
            changed_count = self.fetch_core.get_changed_scale()
            logger.info_service(f"检测到{changed_count}条变更记录")
            
            if changed_count == 0:
                return ReturnModel(
                    status='success',
                    message='没有检测到数据变更',
                    data={'changed_count': 0}
                )
            
            # 2. 获取变更数据
            result = self.fetch_core.get_changed_objects()
            if result.status != 'success':
                return result
            
            file_id = result.data
            
            # 3. 等待文件准备完成
            status_result = self.fetch_core.get_objects_status(file_id)
            if status_result.status != 'success':
                return status_result
            
            # 4. 获取文件下载路径
            file_path_result = self.fetch_core.get_objects_file_path(file_id)
            if file_path_result.status != 'success':
                return file_path_result
            
            file_path_dict = file_path_result.data
            
            # 5. 下载文件
            download_result = self.fetch_core.download_objects(file_path_dict)
            if not download_result.get('success', False):
                return ReturnModel(
                    status='error',
                    message=f'文件下载失败: {download_result.get("message")}',
                    data=None
                )
            
            # 6. 解析文件数据
            structure_data = self._extract_and_parse_structure_files(download_result['file_paths'])
            
            # 7. 更新拉链表数据
            self._update_zipper_tables(structure_data, is_full_update=False)
            
            logger.info_service(f"百度账户{self.user_id}增量更新完成")
            return ReturnModel(
                status='success',
                message=f'百度账户{self.user_id}增量更新成功',
                data={
                    'changed_count': changed_count,
                    'campaign_count': len(structure_data['campaign']),
                    'adgroup_count': len(structure_data['adgroup']),
                    'keyword_count': len(structure_data['keyword']),
                    'creative_count': len(structure_data['creative']),
                    'auto_expansion_count': len(structure_data['autoExpansion'])
                }
            )
            
        except Exception as e:
            logger.error(f"增量更新失败: {e}")
            return ReturnModel(
                status='error',
                message=f'增量更新失败: {str(e)}',
                data=None
            )
    
    def _update_zipper_tables(self, structure_data: Dict[str, List[Dict[str, Any]]], is_full_update: bool = False):
        """更新拉链表数据"""
        try:
            # 更新推广计划
            if structure_data['campaign']:
                campaign_zipper_ops.batch_upsert_campaigns(structure_data['campaign'])
            
            # 更新推广单元
            if structure_data['adgroup']:
                adgroup_zipper_ops.batch_upsert_adgroups(structure_data['adgroup'])
            
            # 更新关键词（普通关键词）
            if structure_data['keyword']:
                keyword_zipper_ops.batch_upsert_keywords(structure_data['keyword'], is_auto_expansion=False)
            
            # 更新关键词（自动扩展关键词）
            if structure_data['autoExpansion']:
                keyword_zipper_ops.batch_upsert_keywords(structure_data['autoExpansion'], is_auto_expansion=True)
            
            # 更新创意
            if structure_data['creative']:
                creative_zipper_ops.batch_upsert_creatives(structure_data['creative'])
            
            logger.info_service("拉链表数据更新完成")
            
        except Exception as e:
            logger.error(f"更新拉链表数据失败: {e}")
            raise
    
    @logger_wrapper(level="INFO_SERVICE")
    def query_current_structure_data(self, data_type: str, **filters) -> List[Dict[str, Any]]:
        """查询当前有效的结构数据"""
        ops_mapping = {
            'campaign': campaign_zipper_ops,
            'adgroup': adgroup_zipper_ops,
            'keyword': keyword_zipper_ops,
            'creative': creative_zipper_ops
        }
        
        if data_type not in ops_mapping:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        ops = ops_mapping[data_type]
        
        with ops.db_client.session_scope as session:
            records = ops.get_current_records(session, **filters)
            return [record.__dict__ for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def query_historical_structure_data(self, data_type: str, start_date: datetime = None, end_date: datetime = None, **filters) -> List[Dict[str, Any]]:
        """查询历史结构数据"""
        ops_mapping = {
            'campaign': campaign_zipper_ops,
            'adgroup': adgroup_zipper_ops,
            'keyword': keyword_zipper_ops,
            'creative': creative_zipper_ops
        }
        
        if data_type not in ops_mapping:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        ops = ops_mapping[data_type]
        
        with ops.db_client.session_scope as session:
            records = ops.get_historical_records(session, start_date, end_date, **filters)
            return [record.__dict__ for record in records]