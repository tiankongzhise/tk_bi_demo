from ..logger import create_logger, logger_wrapper
from ..database.zipper_operations import (
    campaign_zipper_ops,
    adgroup_zipper_ops,
    keyword_zipper_ops,
    creative_zipper_ops
)
from ..database.init_db import db_client
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = create_logger(__name__)


class BaiduDataQueryService:
    """百度广告账户结构查询服务"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_current_campaigns(self) -> List[Dict[str, Any]]:
        """获取当前有效的推广计划结构"""
        with db_client.session_scope() as session:
            records = campaign_zipper_ops.get_current_records(session, user_id=self.user_id)
            return [{
                'campaign_id': record.campaign_id,
                'campaign_name': record.campaign_name,
                'effective_start_date': record.effective_start_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_current_adgroups(self, campaign_id: int = None) -> List[Dict[str, Any]]:
        """获取当前有效的推广单元结构"""
        with db_client.session_scope() as session:
            filters = {'user_id': self.user_id}
            if campaign_id:
                filters['campaign_id'] = campaign_id
                
            records = adgroup_zipper_ops.get_current_records(session, **filters)
            return [{
                'campaign_id': record.campaign_id,
                'adgroup_id': record.adgroup_id,
                'adgroup_name': record.adgroup_name,
                'effective_start_date': record.effective_start_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_current_keywords(self, campaign_id: int = None, adgroup_id: int = None, include_auto_expansion: bool = True) -> List[Dict[str, Any]]:
        """获取当前有效的关键词结构"""
        with db_client.session_scope() as session:
            filters = {'user_id': self.user_id}
            if campaign_id:
                filters['campaign_id'] = campaign_id
            if adgroup_id:
                filters['adgroup_id'] = adgroup_id
            if not include_auto_expansion:
                filters['is_auto_expansion'] = False
                
            records = keyword_zipper_ops.get_current_records(session, **filters)
            return [{
                'campaign_id': record.campaign_id,
                'adgroup_id': record.adgroup_id,
                'keyword_id': record.keyword_id,
                'keyword_text': record.keyword_text,
                'is_auto_expansion': record.is_auto_expansion,
                'effective_start_date': record.effective_start_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_current_creatives(self, campaign_id: int = None, adgroup_id: int = None) -> List[Dict[str, Any]]:
        """获取当前有效的创意结构"""
        with db_client.session_scope() as session:
            filters = {'user_id': self.user_id}
            if campaign_id:
                filters['campaign_id'] = campaign_id
            if adgroup_id:
                filters['adgroup_id'] = adgroup_id
                
            records = creative_zipper_ops.get_current_records(session, **filters)
            return [{
                'campaign_id': record.campaign_id,
                'adgroup_id': record.adgroup_id,
                'creative_id': record.creative_id,
                'title': record.title,
                'description1': record.description1,
                'description2': record.description2,
                'effective_start_date': record.effective_start_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_historical_campaigns(self, campaign_id: int, start_date: datetime = None, 
                               end_date: datetime = None) -> List[Dict[str, Any]]:
        """获取推广计划的历史变更记录"""
        filters = {'user_id': self.user_id, 'campaign_id': campaign_id}
        
        with db_client.session_scope() as session:
            records = campaign_zipper_ops.get_historical_records(session, start_date, end_date, **filters)
            return [{                'campaign_id': record.campaign_id,
                'campaign_name': record.campaign_name,
                'effective_start_date': record.effective_start_date,
                'effective_end_date': record.effective_end_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_historical_adgroups(self, adgroup_id: int, start_date: datetime = None, 
                              end_date: datetime = None) -> List[Dict[str, Any]]:
        """获取推广单元的历史变更记录"""
        filters = {'user_id': self.user_id, 'adgroup_id': adgroup_id}
        
        with db_client.session_scope() as session:
            records = adgroup_zipper_ops.get_historical_records(session, start_date, end_date, **filters)
            return [{
                'campaign_id': record.campaign_id,
                'adgroup_id': record.adgroup_id,
                'adgroup_name': record.adgroup_name,
                'effective_start_date': record.effective_start_date,
                'effective_end_date': record.effective_end_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_historical_keywords(self, keyword_id: int, start_date: datetime = None, 
                              end_date: datetime = None) -> List[Dict[str, Any]]:
        """获取关键词的历史变更记录"""
        filters = {'user_id': self.user_id, 'keyword_id': keyword_id}
        
        with db_client.session_scope() as session:
            records = keyword_zipper_ops.get_historical_records(session, start_date, end_date, **filters)
            return [{
                'campaign_id': record.campaign_id,
                'adgroup_id': record.adgroup_id,
                'keyword_id': record.keyword_id,
                'keyword_text': record.keyword_text,
                'is_auto_expansion': record.is_auto_expansion,
                'effective_start_date': record.effective_start_date,
                'effective_end_date': record.effective_end_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_historical_creatives(self, creative_id: int, start_date: datetime = None, 
                               end_date: datetime = None) -> List[Dict[str, Any]]:
        """获取创意的历史变更记录"""
        filters = {'user_id': self.user_id, 'creative_id': creative_id}
        
        with db_client.session_scope() as session:
            records = creative_zipper_ops.get_historical_records(session, start_date, end_date, **filters)
            return [{
                'campaign_id': record.campaign_id,
                'adgroup_id': record.adgroup_id,
                'creative_id': record.creative_id,
                'title': record.title,
                'description1': record.description1,
                'description2': record.description2,
                'effective_start_date': record.effective_start_date,
                'effective_end_date': record.effective_end_date,
                'data_version': record.data_version
            } for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_data_changes_summary(self, start_date: datetime, end_date: datetime = None) -> Dict[str, Any]:
        """获取指定时间段内的数据变更汇总"""
        if end_date is None:
            end_date = datetime.now()
        
        summary = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'changes': {
                'campaigns': 0,
                'adgroups': 0,
                'keywords': 0,
                'creatives': 0
            }
        }
        
        with db_client.session_scope() as session:
            # 统计各类型数据的变更数量
            for data_type, ops in [
                ('campaigns', campaign_zipper_ops),
                ('adgroups', adgroup_zipper_ops),
                ('keywords', keyword_zipper_ops),
                ('creatives', creative_zipper_ops)
            ]:
                count = session.query(func.count(ops.model_class.id)).filter(
                    and_(
                        ops.model_class.user_id == self.user_id,
                        ops.model_class.effective_start_date >= start_date,
                        ops.model_class.effective_start_date <= end_date,
                        ops.model_class.change_type.in_(['INSERT', 'UPDATE'])
                    )
                ).scalar()
                
                summary['changes'][data_type] = count
        
        return summary
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_account_structure_snapshot(self, snapshot_date: datetime = None) -> Dict[str, Any]:
        """获取指定时间点的账户结构快照"""
        if snapshot_date is None:
            snapshot_date = datetime.now()
        
        snapshot = {
            'snapshot_date': snapshot_date.isoformat(),
            'user_id': self.user_id,
            'structure': {
                'campaigns': [],
                'adgroups': [],
                'keywords': [],
                'creatives': []
            },
            'statistics': {
                'campaign_count': 0,
                'adgroup_count': 0,
                'keyword_count': 0,
                'creative_count': 0,
                'auto_expansion_count': 0
            }
        }
        
        with db_client.session_scope as session:
            # 获取指定时间点有效的数据
            for data_type, ops in [
                ('campaigns', campaign_zipper_ops),
                ('adgroups', adgroup_zipper_ops),
                ('keywords', keyword_zipper_ops),
                ('creatives', creative_zipper_ops)
            ]:
                records = session.query(ops.model_class).filter(
                    and_(
                        ops.model_class.user_id == self.user_id,
                        ops.model_class.effective_start_date <= snapshot_date,
                        or_(
                            ops.model_class.effective_end_date.is_(None),
                            ops.model_class.effective_end_date > snapshot_date
                        )
                    )
                ).all()
                
                snapshot['structure'][data_type] = [self._record_to_dict(record) for record in records]
                
                if data_type == 'keywords':
                    # 统计自动扩展关键词
                    auto_expansion_count = sum(1 for record in records if getattr(record, 'is_auto_expansion', False))
                    snapshot['statistics']['auto_expansion_count'] = auto_expansion_count
                    snapshot['statistics']['keyword_count'] = len(records) - auto_expansion_count
                else:
                    count_key = f"{data_type[:-1]}_count"  # campaigns -> campaign_count
                    snapshot['statistics'][count_key] = len(records)
        
        return snapshot
    
    def _record_to_dict(self, record) -> Dict[str, Any]:
        """将ORM记录转换为字典"""
        result = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    @logger_wrapper(level="INFO_SERVICE")
    def search_keywords_by_text(self, keyword_text: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """根据关键词文本搜索"""
        with db_client.session_scope as session:
            query = session.query(keyword_zipper_ops.model_class).filter(
                and_(
                    keyword_zipper_ops.model_class.user_id == self.user_id,
                    keyword_zipper_ops.model_class.is_current == True
                )
            )
            
            if exact_match:
                query = query.filter(keyword_zipper_ops.model_class.keyword_text == keyword_text)
            else:
                query = query.filter(keyword_zipper_ops.model_class.keyword_text.like(f'%{keyword_text}%'))
            
            records = query.all()
            return [self._record_to_dict(record) for record in records]
    
    @logger_wrapper(level="INFO_SERVICE")
    def get_deleted_entities(self, entity_type: str, start_date: datetime, end_date: datetime = None) -> List[Dict[str, Any]]:
        """获取指定时间段内被删除的实体"""
        if end_date is None:
            end_date = datetime.now()
        
        ops_mapping = {
            'campaign': campaign_zipper_ops,
            'adgroup': adgroup_zipper_ops,
            'keyword': keyword_zipper_ops,
            'creative': creative_zipper_ops
        }
        
        if entity_type not in ops_mapping:
            raise ValueError(f"不支持的实体类型: {entity_type}")
        
        ops = ops_mapping[entity_type]
        
        with db_client.session_scope as session:
            # 查找在指定时间段内结束的记录（被删除或更新的记录）
            records = session.query(ops.model_class).filter(
                and_(
                    ops.model_class.user_id == self.user_id,
                    ops.model_class.effective_end_date.isnot(None),
                    ops.model_class.effective_end_date >= start_date,
                    ops.model_class.effective_end_date <= end_date
                )
            ).all()
            
            return [self._record_to_dict(record) for record in records]