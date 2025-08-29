from .init_db import db_client
from .zipper_schemas import (
    BaiduCampaignZipper,
    BaiduAdgroupZipper, 
    BaiduKeywordZipper,
    BaiduCreativeZipper
)
from ..logger import create_logger, logger_wrapper
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
import hashlib
import json

logger = create_logger(__name__)


class ZipperTableOperations:
    """拉链表操作基类"""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.table_name = model_class.__tablename__
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """计算数据哈希值，用于检测数据变化"""
        # 排除时间戳等变化字段
        exclude_fields = {'create_at', 'update_at', 'effective_start_date', 'effective_end_date', 'is_current', 'data_version'}
        filtered_data = {k: v for k, v in data.items() if k not in exclude_fields}
        data_str = json.dumps(filtered_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    @logger_wrapper(level="INFO_DATABASE")
    def get_current_records(self, session: Session, **filters) -> List:
        """获取当前有效记录"""
        query = session.query(self.model_class).filter(
            self.model_class.is_current == True
        )
        
        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.filter(getattr(self.model_class, field) == value)
        
        return query.all()
    
    @logger_wrapper(level="INFO_DATABASE")
    def get_historical_records(self, session: Session, start_date: datetime = None, end_date: datetime = None, **filters) -> List:
        """获取历史记录"""
        query = session.query(self.model_class)
        
        if start_date:
            query = query.filter(self.model_class.effective_start_date >= start_date)
        if end_date:
            query = query.filter(
                or_(
                    self.model_class.effective_end_date <= end_date,
                    self.model_class.effective_end_date.is_(None)
                )
            )
        
        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.filter(getattr(self.model_class, field) == value)
        
        return query.order_by(self.model_class.effective_start_date.desc()).all()
    
    @logger_wrapper(level="INFO_DATABASE")
    def close_current_record(self, session: Session, record_id: int, end_date: datetime):
        """关闭当前有效记录"""
        session.execute(
            update(self.model_class)
            .where(self.model_class.id == record_id)
            .values(
                effective_end_date=end_date,
                is_current=False,
                update_at=datetime.now()
            )
        )
    
    @logger_wrapper(level="INFO_DATABASE")
    def insert_new_record(self, session: Session, data: Dict[str, Any], change_type: str = "INSERT"):
        """插入新记录"""
        current_time = datetime.now()
        
        # 设置拉链表字段
        data.update({
            'effective_start_date': current_time,
            'effective_end_date': None,
            'is_current': True,
            'change_type': change_type,
            'create_at': current_time
        })
        
        new_record = self.model_class(**data)
        session.add(new_record)
        return new_record
    
    @logger_wrapper(level="INFO_DATABASE")
    def upsert_record(self, session: Session, business_keys: Dict[str, Any], data: Dict[str, Any]):
        """更新或插入记录（拉链表核心逻辑）"""
        # 查找当前有效记录
        current_record = session.query(self.model_class).filter(
            and_(
                self.model_class.is_current == True,
                *[getattr(self.model_class, k) == v for k, v in business_keys.items()]
            )
        ).first()
        
        current_time = datetime.now()
        
        if current_record is None:
            # 没有当前记录，直接插入
            logger.info_database(f"插入新记录到{self.table_name}: {business_keys}")
            return self.insert_new_record(session, {**business_keys, **data}, "INSERT")
        else:
            # 检查数据是否有变化
            current_hash = self._calculate_data_hash(current_record.__dict__)
            new_hash = self._calculate_data_hash({**business_keys, **data})
            
            if current_hash != new_hash:
                # 数据有变化，关闭当前记录并插入新记录
                logger.info_database(f"数据有变化，更新{self.table_name}: {business_keys}")
                self.close_current_record(session, current_record.id, current_time)
                
                # 增加版本号
                new_version = current_record.data_version + 1
                data['data_version'] = new_version
                
                return self.insert_new_record(session, {**business_keys, **data}, "UPDATE")
            else:
                # 数据无变化，不做处理
                logger.info_database(f"数据无变化，跳过{self.table_name}: {business_keys}")
                return current_record


class BaiduCampaignZipperOps(ZipperTableOperations):
    """百度推广计划拉链表操作"""
    
    def __init__(self):
        super().__init__(BaiduCampaignZipper)
    
    @logger_wrapper(level="INFO_DATABASE")
    def batch_upsert_campaigns(self, campaigns_data: List[Dict[str, Any]]):
        """批量更新推广计划数据"""
        with db_client.session_scope as session:
            for campaign_data in campaigns_data:
                business_keys = {
                    'user_name': campaign_data['user_name'],
                    'campaign_id': campaign_data['campaign_id']
                }
                
                # 提取业务字段
                data = {
                    'campaign_name': campaign_data.get('campaign_name'),
                    'status': campaign_data.get('status'),
                    'budget': campaign_data.get('budget'),
                    'schedule': campaign_data.get('schedule'),
                    'target_setting': campaign_data.get('target_setting'),
                    'raw_data': campaign_data
                }
                
                self.upsert_record(session, business_keys, data)
            
            session.commit()
            logger.info_database(f"批量更新推广计划完成，共处理{len(campaigns_data)}条记录")


class BaiduAdgroupZipperOps(ZipperTableOperations):
    """百度推广单元拉链表操作"""
    
    def __init__(self):
        super().__init__(BaiduAdgroupZipper)
    
    @logger_wrapper(level="INFO_DATABASE")
    def batch_upsert_adgroups(self, adgroups_data: List[Dict[str, Any]]):
        """批量更新推广单元数据"""
        with db_client.session_scope as session:
            for adgroup_data in adgroups_data:
                business_keys = {
                    'user_name': adgroup_data['user_name'],
                    'campaign_id': adgroup_data['campaign_id'],
                    'adgroup_id': adgroup_data['adgroup_id']
                }
                
                data = {
                    'adgroup_name': adgroup_data.get('adgroup_name'),
                    'status': adgroup_data.get('status'),
                    'max_price': adgroup_data.get('max_price'),
                    'negative_words': adgroup_data.get('negative_words'),
                    'exact_negative_words': adgroup_data.get('exact_negative_words'),
                    'raw_data': adgroup_data
                }
                
                self.upsert_record(session, business_keys, data)
            
            session.commit()
            logger.info_database(f"批量更新推广单元完成，共处理{len(adgroups_data)}条记录")


class BaiduKeywordZipperOps(ZipperTableOperations):
    """百度关键词拉链表操作（包含autoExpansion）"""
    
    def __init__(self):
        super().__init__(BaiduKeywordZipper)
    
    @logger_wrapper(level="INFO_DATABASE")
    def batch_upsert_keywords(self, keywords_data: List[Dict[str, Any]], is_auto_expansion: bool = False):
        """批量更新关键词数据"""
        with db_client.session_scope as session:
            for keyword_data in keywords_data:
                business_keys = {
                    'user_name': keyword_data['user_name'],
                    'campaign_id': keyword_data['campaign_id'],
                    'adgroup_id': keyword_data['adgroup_id'],
                    'keyword_id': keyword_data['keyword_id']
                }
                
                data = {
                    'keyword_text': keyword_data.get('keyword_text'),
                    'status': keyword_data.get('status'),
                    'match_type': keyword_data.get('match_type'),
                    'price': keyword_data.get('price'),
                    'destination_url': keyword_data.get('destination_url'),
                    'is_auto_expansion': is_auto_expansion,
                    'raw_data': keyword_data
                }
                
                self.upsert_record(session, business_keys, data)
            
            session.commit()
            logger.info_database(f"批量更新关键词完成，共处理{len(keywords_data)}条记录，autoExpansion: {is_auto_expansion}")


class BaiduCreativeZipperOps(ZipperTableOperations):
    """百度创意拉链表操作"""
    
    def __init__(self):
        super().__init__(BaiduCreativeZipper)
    
    @logger_wrapper(level="INFO_DATABASE")
    def batch_upsert_creatives(self, creatives_data: List[Dict[str, Any]]):
        """批量更新创意数据"""
        with db_client.session_scope as session:
            for creative_data in creatives_data:
                business_keys = {
                    'user_name': creative_data['user_name'],
                    'campaign_id': creative_data['campaign_id'],
                    'adgroup_id': creative_data['adgroup_id'],
                    'creative_id': creative_data['creative_id']
                }
                
                data = {
                    'title': creative_data.get('title'),
                    'description1': creative_data.get('description1'),
                    'description2': creative_data.get('description2'),
                    'destination_url': creative_data.get('destination_url'),
                    'display_url': creative_data.get('display_url'),
                    'status': creative_data.get('status'),
                    'raw_data': creative_data
                }
                
                self.upsert_record(session, business_keys, data)
            
            session.commit()
            logger.info_database(f"批量更新创意完成，共处理{len(creatives_data)}条记录")


# 创建操作实例
campaign_zipper_ops = BaiduCampaignZipperOps()
adgroup_zipper_ops = BaiduAdgroupZipperOps()
keyword_zipper_ops = BaiduKeywordZipperOps()
creative_zipper_ops = BaiduCreativeZipperOps()