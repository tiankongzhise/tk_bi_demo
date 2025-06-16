"""数据处理服务模块

提供数据验证、转换、清洗和存储功能。
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date
from decimal import Decimal
import json

from sqlalchemy import select, insert, update, delete
from sqlalchemy.dialects.mysql import insert as mysql_insert
from pydantic import ValidationError

from ..core import (
    get_database_manager,
    get_logger,
    DataValidationException,
    DatabaseException
)
from ..models import (
    AdData,
    AdReportModel,
    AdMetrics,
    DataQuality,
    PlatformEnum,
    DataStatusEnum
)
from ..utils.validators import DataValidator

logger = get_logger(__name__)


class DataProcessor:
    """数据处理器
    
    负责广告数据的验证、转换、清洗和存储。
    """
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.validator = DataValidator()
        self._batch_size = 1000
    
    async def process_ad_data(
        self, 
        raw_data: List[Dict[str, Any]], 
        platform: PlatformEnum,
        report_date: date
    ) -> Tuple[int, int, List[str]]:
        """处理广告数据
        
        Args:
            raw_data: 原始数据列表
            platform: 广告平台
            report_date: 报表日期
            
        Returns:
            Tuple[int, int, List[str]]: (成功数量, 失败数量, 错误信息列表)
        """
        logger.info(
            f"开始处理{platform.value}平台数据",
            extra={
                "platform": platform.value,
                "report_date": report_date.isoformat(),
                "total_records": len(raw_data)
            }
        )
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        # 分批处理数据
        for i in range(0, len(raw_data), self._batch_size):
            batch = raw_data[i:i + self._batch_size]
            
            try:
                batch_success, batch_errors = await self._process_batch(
                    batch, platform, report_date
                )
                success_count += batch_success
                error_count += len(batch_errors)
                error_messages.extend(batch_errors)
                
                logger.debug(
                    f"批次处理完成",
                    extra={
                        "batch_index": i // self._batch_size + 1,
                        "batch_size": len(batch),
                        "success_count": batch_success,
                        "error_count": len(batch_errors)
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"批次处理失败: {e}",
                    extra={
                        "batch_index": i // self._batch_size + 1,
                        "batch_size": len(batch),
                        "error": str(e)
                    }
                )
                error_count += len(batch)
                error_messages.append(f"批次{i // self._batch_size + 1}处理失败: {e}")
        
        # 记录数据质量
        await self._record_data_quality(
            platform, report_date, success_count, error_count, error_messages
        )
        
        logger.info(
            f"{platform.value}平台数据处理完成",
            extra={
                "platform": platform.value,
                "report_date": report_date.isoformat(),
                "success_count": success_count,
                "error_count": error_count,
                "total_records": len(raw_data)
            }
        )
        
        return success_count, error_count, error_messages
    
    async def _process_batch(
        self, 
        batch_data: List[Dict[str, Any]], 
        platform: PlatformEnum,
        report_date: date
    ) -> Tuple[int, List[str]]:
        """处理数据批次
        
        Args:
            batch_data: 批次数据
            platform: 广告平台
            report_date: 报表日期
            
        Returns:
            Tuple[int, List[str]]: (成功数量, 错误信息列表)
        """
        validated_data = []
        error_messages = []
        
        # 数据验证和转换
        for i, raw_record in enumerate(batch_data):
            try:
                # 添加平台和日期信息
                raw_record["platform"] = platform.value
                raw_record["report_date"] = report_date
                
                # 数据验证
                validated_record = await self._validate_record(raw_record)
                validated_data.append(validated_record)
                
            except ValidationError as e:
                error_msg = f"记录{i+1}验证失败: {e}"
                error_messages.append(error_msg)
                logger.warning(error_msg, extra={"record_index": i, "raw_data": raw_record})
            
            except Exception as e:
                error_msg = f"记录{i+1}处理失败: {e}"
                error_messages.append(error_msg)
                logger.error(error_msg, extra={"record_index": i, "error": str(e)})
        
        # 批量存储
        if validated_data:
            try:
                await self._batch_insert(validated_data)
                logger.debug(f"批量插入{len(validated_data)}条记录成功")
            except Exception as e:
                error_msg = f"批量插入失败: {e}"
                error_messages.append(error_msg)
                logger.error(error_msg)
                return 0, error_messages
        
        return len(validated_data), error_messages
    
    async def _validate_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """验证单条记录
        
        Args:
            raw_record: 原始记录
            
        Returns:
            Dict[str, Any]: 验证后的记录
            
        Raises:
            ValidationError: 验证失败
        """
        # 使用Pydantic模型验证
        ad_report = AdReportModel(**raw_record)
        
        # 数据清洗和转换
        cleaned_data = {
            "platform": ad_report.platform,
            "account_id": ad_report.account_id,
            "campaign_id": ad_report.campaign_id,
            "campaign_name": self._clean_text(ad_report.campaign_name),
            "adgroup_id": ad_report.adgroup_id,
            "adgroup_name": self._clean_text(ad_report.adgroup_name),
            "keyword_id": ad_report.keyword_id,
            "keyword": self._clean_text(ad_report.keyword),
            "match_type": ad_report.match_type,
            "device_type": ad_report.device_type,
            "report_date": ad_report.report_date,
            "impressions": ad_report.metrics.impressions,
            "clicks": ad_report.metrics.clicks,
            "cost": float(ad_report.metrics.cost),
            "conversions": ad_report.metrics.conversions,
            "conversion_value": float(ad_report.metrics.conversion_value) if ad_report.metrics.conversion_value else 0.0,
            "ctr": float(ad_report.metrics.ctr),
            "cpc": float(ad_report.metrics.cpc),
            "cpm": float(ad_report.metrics.cpm),
            "cvr": float(ad_report.metrics.cvr),
            "roas": float(ad_report.metrics.roas),
            "data_status": DataStatusEnum.ACTIVE.value,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # 自定义验证规则
        await self.validator.validate_ad_data(cleaned_data)
        
        return cleaned_data
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """清洗文本数据
        
        Args:
            text: 原始文本
            
        Returns:
            Optional[str]: 清洗后的文本
        """
        if not text:
            return None
        
        # 去除首尾空格
        text = text.strip()
        
        # 替换特殊字符
        text = text.replace("\x00", "")  # 去除NULL字符
        text = text.replace("\r\n", " ")  # 替换换行符
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")
        
        # 限制长度
        if len(text) > 255:
            text = text[:252] + "..."
        
        return text if text else None
    
    async def _batch_insert(self, data_list: List[Dict[str, Any]]) -> None:
        """批量插入数据
        
        Args:
            data_list: 数据列表
            
        Raises:
            DatabaseException: 数据库操作异常
        """
        try:
            async with self.db_manager.get_session() as session:
                # 使用MySQL的ON DUPLICATE KEY UPDATE
                stmt = mysql_insert(AdData).values(data_list)
                
                # 定义更新字段（排除主键和创建时间）
                update_dict = {
                    col.name: stmt.inserted[col.name]
                    for col in AdData.__table__.columns
                    if col.name not in ['id', 'created_at']
                }
                update_dict['updated_at'] = datetime.now()
                
                stmt = stmt.on_duplicate_key_update(**update_dict)
                
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            logger.error(f"批量插入数据失败: {e}")
            raise DatabaseException(
                f"批量插入数据失败: {e}",
                operation="batch_insert",
                error_code=2002
            )
    
    async def _record_data_quality(
        self,
        platform: PlatformEnum,
        report_date: date,
        success_count: int,
        error_count: int,
        error_messages: List[str]
    ) -> None:
        """记录数据质量信息
        
        Args:
            platform: 广告平台
            report_date: 报表日期
            success_count: 成功数量
            error_count: 错误数量
            error_messages: 错误信息列表
        """
        try:
            total_count = success_count + error_count
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            quality_data = {
                "check_time": datetime.now(),
                "platform": platform.value,
                "check_type": "data_processing",
                "result": "pass" if error_count == 0 else "warning" if success_rate >= 90 else "fail",
                "total_records": total_count,
                "success_records": success_count,
                "error_records": error_count,
                "success_rate": success_rate,
                "error_details": json.dumps(error_messages[:10], ensure_ascii=False) if error_messages else None,
                "report_date": report_date
            }
            
            async with self.db_manager.get_session() as session:
                stmt = insert(DataQuality).values(quality_data)
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            logger.error(f"记录数据质量信息失败: {e}")
    
    async def get_data_statistics(
        self, 
        platform: Optional[PlatformEnum] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取数据统计信息
        
        Args:
            platform: 广告平台
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            async with self.db_manager.get_session() as session:
                # 构建查询条件
                conditions = []
                if platform:
                    conditions.append(AdData.platform == platform.value)
                if start_date:
                    conditions.append(AdData.report_date >= start_date)
                if end_date:
                    conditions.append(AdData.report_date <= end_date)
                
                # 基础统计查询
                from sqlalchemy import func
                
                base_query = select(
                    func.count(AdData.id).label('total_records'),
                    func.sum(AdData.impressions).label('total_impressions'),
                    func.sum(AdData.clicks).label('total_clicks'),
                    func.sum(AdData.cost).label('total_cost'),
                    func.sum(AdData.conversions).label('total_conversions'),
                    func.sum(AdData.conversion_value).label('total_conversion_value'),
                    func.avg(AdData.ctr).label('avg_ctr'),
                    func.avg(AdData.cpc).label('avg_cpc'),
                    func.avg(AdData.cvr).label('avg_cvr'),
                    func.avg(AdData.roas).label('avg_roas')
                )
                
                if conditions:
                    base_query = base_query.where(*conditions)
                
                result = await session.execute(base_query)
                stats = result.first()
                
                # 按平台统计
                platform_query = select(
                    AdData.platform,
                    func.count(AdData.id).label('records'),
                    func.sum(AdData.cost).label('cost')
                ).group_by(AdData.platform)
                
                if conditions:
                    platform_query = platform_query.where(*conditions)
                
                platform_result = await session.execute(platform_query)
                platform_stats = {
                    row.platform: {
                        'records': row.records,
                        'cost': float(row.cost) if row.cost else 0
                    }
                    for row in platform_result
                }
                
                return {
                    "total_records": stats.total_records or 0,
                    "total_impressions": stats.total_impressions or 0,
                    "total_clicks": stats.total_clicks or 0,
                    "total_cost": float(stats.total_cost) if stats.total_cost else 0,
                    "total_conversions": stats.total_conversions or 0,
                    "total_conversion_value": float(stats.total_conversion_value) if stats.total_conversion_value else 0,
                    "avg_ctr": float(stats.avg_ctr) if stats.avg_ctr else 0,
                    "avg_cpc": float(stats.avg_cpc) if stats.avg_cpc else 0,
                    "avg_cvr": float(stats.avg_cvr) if stats.avg_cvr else 0,
                    "avg_roas": float(stats.avg_roas) if stats.avg_roas else 0,
                    "platform_stats": platform_stats
                }
                
        except Exception as e:
            logger.error(f"获取数据统计失败: {e}")
            raise DatabaseException(
                f"获取数据统计失败: {e}",
                operation="get_statistics",
                error_code=2003
            )
    
    async def cleanup_old_data(
        self, 
        days_to_keep: int = 90,
        platform: Optional[PlatformEnum] = None
    ) -> int:
        """清理旧数据
        
        Args:
            days_to_keep: 保留天数
            platform: 指定平台（可选）
            
        Returns:
            int: 删除的记录数
        """
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
            
            async with self.db_manager.get_session() as session:
                conditions = [AdData.report_date < cutoff_date]
                if platform:
                    conditions.append(AdData.platform == platform.value)
                
                # 先查询要删除的记录数
                count_query = select(func.count(AdData.id)).where(*conditions)
                count_result = await session.execute(count_query)
                delete_count = count_result.scalar()
                
                if delete_count > 0:
                    # 执行删除
                    delete_stmt = delete(AdData).where(*conditions)
                    await session.execute(delete_stmt)
                    await session.commit()
                    
                    logger.info(
                        f"清理旧数据完成",
                        extra={
                            "platform": platform.value if platform else "all",
                            "cutoff_date": cutoff_date.isoformat(),
                            "deleted_records": delete_count
                        }
                    )
                
                return delete_count
                
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            raise DatabaseException(
                f"清理旧数据失败: {e}",
                operation="cleanup_data",
                error_code=2004
            )
    
    async def export_data(
        self,
        platform: Optional[PlatformEnum] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format_type: str = "json"
    ) -> Union[List[Dict[str, Any]], str]:
        """导出数据
        
        Args:
            platform: 广告平台
            start_date: 开始日期
            end_date: 结束日期
            format_type: 导出格式（json/csv）
            
        Returns:
            Union[List[Dict[str, Any]], str]: 导出的数据
        """
        try:
            async with self.db_manager.get_session() as session:
                # 构建查询
                query = select(AdData)
                
                conditions = []
                if platform:
                    conditions.append(AdData.platform == platform.value)
                if start_date:
                    conditions.append(AdData.report_date >= start_date)
                if end_date:
                    conditions.append(AdData.report_date <= end_date)
                
                if conditions:
                    query = query.where(*conditions)
                
                query = query.order_by(AdData.report_date.desc(), AdData.platform)
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                # 转换为字典格式
                data_list = []
                for record in records:
                    data_dict = {
                        "id": record.id,
                        "platform": record.platform,
                        "account_id": record.account_id,
                        "campaign_id": record.campaign_id,
                        "campaign_name": record.campaign_name,
                        "adgroup_id": record.adgroup_id,
                        "adgroup_name": record.adgroup_name,
                        "keyword_id": record.keyword_id,
                        "keyword": record.keyword,
                        "match_type": record.match_type,
                        "device_type": record.device_type,
                        "report_date": record.report_date.isoformat(),
                        "impressions": record.impressions,
                        "clicks": record.clicks,
                        "cost": record.cost,
                        "conversions": record.conversions,
                        "conversion_value": record.conversion_value,
                        "ctr": record.ctr,
                        "cpc": record.cpc,
                        "cpm": record.cpm,
                        "cvr": record.cvr,
                        "roas": record.roas,
                        "created_at": record.created_at.isoformat(),
                        "updated_at": record.updated_at.isoformat()
                    }
                    data_list.append(data_dict)
                
                if format_type == "csv":
                    import csv
                    import io
                    
                    output = io.StringIO()
                    if data_list:
                        writer = csv.DictWriter(output, fieldnames=data_list[0].keys())
                        writer.writeheader()
                        writer.writerows(data_list)
                    
                    return output.getvalue()
                
                return data_list
                
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise DatabaseException(
                f"导出数据失败: {e}",
                operation="export_data",
                error_code=2005
            )


# 全局数据处理器实例
_data_processor = None


async def get_data_processor() -> DataProcessor:
    """获取数据处理器实例
    
    Returns:
        DataProcessor: 数据处理器实例
    """
    global _data_processor
    if _data_processor is None:
        _data_processor = DataProcessor()
    return _data_processor