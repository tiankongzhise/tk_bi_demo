"""日期处理工具类"""

from datetime import datetime, timedelta
from typing import Tuple


class DateRangeProcessor:
    """日期范围处理器"""
    
    @staticmethod
    def process_date_range(date_range: str) -> Tuple[str, str]:
        """处理日期范围，返回(startDate, endDate)
        
        Args:
            date_range: 日期范围类型
            
        Returns:
            Tuple[str, str]: (startDate, endDate)
        """
        today = datetime.now().date()
        
        if date_range == "today":
            start_date = today
            end_date = today
        elif date_range == "yesterday":
            start_date = today - timedelta(days=1)
            end_date = today - timedelta(days=1)
        elif date_range == "7days":
            start_date = today - timedelta(days=7)
            end_date = today - timedelta(days=1)
        elif date_range == "30days":
            start_date = today - timedelta(days=30)
            end_date = today - timedelta(days=1)
        elif date_range == "week":
            # 本周一到昨天
            days_since_monday = today.weekday()
            start_date = today - timedelta(days=days_since_monday)
            end_date = today - timedelta(days=1)
            if end_date < start_date:
                end_date = start_date
        elif date_range == "month":
            # 本月1号到昨天
            start_date = today.replace(day=1)
            end_date = today - timedelta(days=1)
            if end_date < start_date:
                end_date = start_date
        elif date_range == "week_today":
            # 本周一到今天
            days_since_monday = today.weekday()
            start_date = today - timedelta(days=days_since_monday)
            end_date = today
        elif date_range == "month_today":
            # 本月1号到今天
            start_date = today.replace(day=1)
            end_date = today
        else:
            raise ValueError(f"不支持的日期范围类型: {date_range}")
        
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    
    @staticmethod
    def add_time_suffix(start_date: str, end_date: str, time_unit: str) -> Tuple[str, str]:
        """为日期添加时间后缀
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            time_unit: 时间单位
            
        Returns:
            Tuple[str, str]: 处理后的(startDate, endDate)
        """
        if time_unit == "HOUR":
            if " " not in start_date:
                start_date += " 00:00:00"
            if " " not in end_date:
                end_date += " 23:59:59"
        
        return start_date, end_date
