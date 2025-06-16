"""日期时间工具模块

提供日期时间处理相关功能。
"""

import pytz
from datetime import datetime, date, timedelta, timezone
from typing import Optional, Union, List, Tuple
from dateutil import parser
from dateutil.relativedelta import relativedelta

from ..core import get_logger

logger = get_logger(__name__)


class DateTimeUtils:
    """日期时间工具类
    
    提供各种日期时间处理功能。
    """
    
    # 常用时区
    TIMEZONE_CHINA = pytz.timezone('Asia/Shanghai')
    TIMEZONE_UTC = pytz.UTC
    TIMEZONE_US_EAST = pytz.timezone('US/Eastern')
    TIMEZONE_US_WEST = pytz.timezone('US/Pacific')
    
    # 常用日期格式
    FORMAT_DATE = "%Y-%m-%d"
    FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S"
    FORMAT_DATETIME_MS = "%Y-%m-%d %H:%M:%S.%f"
    FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"
    FORMAT_ISO_MS = "%Y-%m-%dT%H:%M:%S.%f"
    FORMAT_COMPACT = "%Y%m%d"
    FORMAT_COMPACT_DATETIME = "%Y%m%d%H%M%S"
    
    @classmethod
    def now(cls, tz: Optional[pytz.BaseTzInfo] = None) -> datetime:
        """获取当前时间
        
        Args:
            tz: 时区，默认为中国时区
            
        Returns:
            datetime: 当前时间
        """
        if tz is None:
            tz = cls.TIMEZONE_CHINA
        return datetime.now(tz)
    
    @classmethod
    def utc_now(cls) -> datetime:
        """获取当前UTC时间
        
        Returns:
            datetime: 当前UTC时间
        """
        return datetime.now(cls.TIMEZONE_UTC)
    
    @classmethod
    def today(cls, tz: Optional[pytz.BaseTzInfo] = None) -> date:
        """获取今天日期
        
        Args:
            tz: 时区，默认为中国时区
            
        Returns:
            date: 今天日期
        """
        return cls.now(tz).date()
    
    @classmethod
    def yesterday(cls, tz: Optional[pytz.BaseTzInfo] = None) -> date:
        """获取昨天日期
        
        Args:
            tz: 时区，默认为中国时区
            
        Returns:
            date: 昨天日期
        """
        return cls.today(tz) - timedelta(days=1)
    
    @classmethod
    def tomorrow(cls, tz: Optional[pytz.BaseTzInfo] = None) -> date:
        """获取明天日期
        
        Args:
            tz: 时区，默认为中国时区
            
        Returns:
            date: 明天日期
        """
        return cls.today(tz) + timedelta(days=1)
    
    @classmethod
    def parse_date(cls, date_string: str, format_str: Optional[str] = None) -> Optional[date]:
        """解析日期字符串
        
        Args:
            date_string: 日期字符串
            format_str: 日期格式，如果为None则自动解析
            
        Returns:
            Optional[date]: 解析后的日期，失败返回None
        """
        if not date_string:
            return None
        
        try:
            if format_str:
                return datetime.strptime(date_string, format_str).date()
            else:
                # 使用dateutil自动解析
                return parser.parse(date_string).date()
        except (ValueError, TypeError) as e:
            logger.warning(f"日期解析失败: {date_string}, 错误: {str(e)}")
            return None
    
    @classmethod
    def parse_datetime(cls, datetime_string: str, format_str: Optional[str] = None, tz: Optional[pytz.BaseTzInfo] = None) -> Optional[datetime]:
        """解析日期时间字符串
        
        Args:
            datetime_string: 日期时间字符串
            format_str: 日期时间格式，如果为None则自动解析
            tz: 时区，如果为None且解析结果没有时区信息，则使用中国时区
            
        Returns:
            Optional[datetime]: 解析后的日期时间，失败返回None
        """
        if not datetime_string:
            return None
        
        try:
            if format_str:
                dt = datetime.strptime(datetime_string, format_str)
            else:
                # 使用dateutil自动解析
                dt = parser.parse(datetime_string)
            
            # 如果没有时区信息，添加默认时区
            if dt.tzinfo is None:
                if tz is None:
                    tz = cls.TIMEZONE_CHINA
                dt = tz.localize(dt)
            
            return dt
        except (ValueError, TypeError) as e:
            logger.warning(f"日期时间解析失败: {datetime_string}, 错误: {str(e)}")
            return None
    
    @classmethod
    def format_date(cls, date_obj: Union[date, datetime], format_str: str = FORMAT_DATE) -> str:
        """格式化日期
        
        Args:
            date_obj: 日期或日期时间对象
            format_str: 格式字符串
            
        Returns:
            str: 格式化后的日期字符串
        """
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        return date_obj.strftime(format_str)
    
    @classmethod
    def format_datetime(cls, datetime_obj: datetime, format_str: str = FORMAT_DATETIME) -> str:
        """格式化日期时间
        
        Args:
            datetime_obj: 日期时间对象
            format_str: 格式字符串
            
        Returns:
            str: 格式化后的日期时间字符串
        """
        return datetime_obj.strftime(format_str)
    
    @classmethod
    def convert_timezone(cls, dt: datetime, target_tz: pytz.BaseTzInfo) -> datetime:
        """转换时区
        
        Args:
            dt: 日期时间对象
            target_tz: 目标时区
            
        Returns:
            datetime: 转换后的日期时间
        """
        if dt.tzinfo is None:
            # 如果没有时区信息，假设为中国时区
            dt = cls.TIMEZONE_CHINA.localize(dt)
        
        return dt.astimezone(target_tz)
    
    @classmethod
    def to_utc(cls, dt: datetime) -> datetime:
        """转换为UTC时间
        
        Args:
            dt: 日期时间对象
            
        Returns:
            datetime: UTC时间
        """
        return cls.convert_timezone(dt, cls.TIMEZONE_UTC)
    
    @classmethod
    def to_china_time(cls, dt: datetime) -> datetime:
        """转换为中国时间
        
        Args:
            dt: 日期时间对象
            
        Returns:
            datetime: 中国时间
        """
        return cls.convert_timezone(dt, cls.TIMEZONE_CHINA)
    
    @classmethod
    def get_date_range(cls, start_date: Union[str, date], end_date: Union[str, date]) -> List[date]:
        """获取日期范围内的所有日期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[date]: 日期列表
        """
        if isinstance(start_date, str):
            start_date = cls.parse_date(start_date)
        if isinstance(end_date, str):
            end_date = cls.parse_date(end_date)
        
        if not start_date or not end_date:
            return []
        
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        return dates
    
    @classmethod
    def get_week_range(cls, target_date: Union[str, date] = None) -> Tuple[date, date]:
        """获取指定日期所在周的开始和结束日期（周一到周日）
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            Tuple[date, date]: (周开始日期, 周结束日期)
        """
        if target_date is None:
            target_date = cls.today()
        elif isinstance(target_date, str):
            target_date = cls.parse_date(target_date)
        
        if not target_date:
            raise ValueError("无效的日期")
        
        # 获取周一（weekday()返回0-6，0是周一）
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    
    @classmethod
    def get_month_range(cls, target_date: Union[str, date] = None) -> Tuple[date, date]:
        """获取指定日期所在月的开始和结束日期
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            Tuple[date, date]: (月开始日期, 月结束日期)
        """
        if target_date is None:
            target_date = cls.today()
        elif isinstance(target_date, str):
            target_date = cls.parse_date(target_date)
        
        if not target_date:
            raise ValueError("无效的日期")
        
        # 月初
        month_start = target_date.replace(day=1)
        
        # 月末
        next_month = month_start + relativedelta(months=1)
        month_end = next_month - timedelta(days=1)
        
        return month_start, month_end
    
    @classmethod
    def get_quarter_range(cls, target_date: Union[str, date] = None) -> Tuple[date, date]:
        """获取指定日期所在季度的开始和结束日期
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            Tuple[date, date]: (季度开始日期, 季度结束日期)
        """
        if target_date is None:
            target_date = cls.today()
        elif isinstance(target_date, str):
            target_date = cls.parse_date(target_date)
        
        if not target_date:
            raise ValueError("无效的日期")
        
        # 计算季度
        quarter = (target_date.month - 1) // 3 + 1
        
        # 季度开始月份
        quarter_start_month = (quarter - 1) * 3 + 1
        quarter_start = target_date.replace(month=quarter_start_month, day=1)
        
        # 季度结束日期
        quarter_end_month = quarter * 3
        quarter_end = target_date.replace(month=quarter_end_month, day=1)
        quarter_end = quarter_end + relativedelta(months=1) - timedelta(days=1)
        
        return quarter_start, quarter_end
    
    @classmethod
    def get_year_range(cls, target_date: Union[str, date] = None) -> Tuple[date, date]:
        """获取指定日期所在年的开始和结束日期
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            Tuple[date, date]: (年开始日期, 年结束日期)
        """
        if target_date is None:
            target_date = cls.today()
        elif isinstance(target_date, str):
            target_date = cls.parse_date(target_date)
        
        if not target_date:
            raise ValueError("无效的日期")
        
        year_start = target_date.replace(month=1, day=1)
        year_end = target_date.replace(month=12, day=31)
        
        return year_start, year_end
    
    @classmethod
    def get_last_n_days(cls, n: int, end_date: Union[str, date] = None) -> List[date]:
        """获取最近N天的日期列表
        
        Args:
            n: 天数
            end_date: 结束日期，默认为今天
            
        Returns:
            List[date]: 日期列表
        """
        if end_date is None:
            end_date = cls.today()
        elif isinstance(end_date, str):
            end_date = cls.parse_date(end_date)
        
        if not end_date:
            raise ValueError("无效的结束日期")
        
        start_date = end_date - timedelta(days=n-1)
        return cls.get_date_range(start_date, end_date)
    
    @classmethod
    def get_business_days(cls, start_date: Union[str, date], end_date: Union[str, date]) -> List[date]:
        """获取日期范围内的工作日（周一到周五）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[date]: 工作日列表
        """
        all_dates = cls.get_date_range(start_date, end_date)
        # 过滤出工作日（周一到周五，weekday()返回0-4）
        return [d for d in all_dates if d.weekday() < 5]
    
    @classmethod
    def is_business_day(cls, target_date: Union[str, date]) -> bool:
        """判断是否为工作日
        
        Args:
            target_date: 目标日期
            
        Returns:
            bool: 是否为工作日
        """
        if isinstance(target_date, str):
            target_date = cls.parse_date(target_date)
        
        if not target_date:
            return False
        
        return target_date.weekday() < 5
    
    @classmethod
    def add_business_days(cls, start_date: Union[str, date], days: int) -> date:
        """在指定日期基础上增加工作日
        
        Args:
            start_date: 开始日期
            days: 要增加的工作日数
            
        Returns:
            date: 结果日期
        """
        if isinstance(start_date, str):
            start_date = cls.parse_date(start_date)
        
        if not start_date:
            raise ValueError("无效的开始日期")
        
        current_date = start_date
        added_days = 0
        
        while added_days < days:
            current_date += timedelta(days=1)
            if cls.is_business_day(current_date):
                added_days += 1
        
        return current_date
    
    @classmethod
    def get_timestamp(cls, dt: Optional[datetime] = None) -> int:
        """获取时间戳（秒）
        
        Args:
            dt: 日期时间对象，默认为当前时间
            
        Returns:
            int: 时间戳
        """
        if dt is None:
            dt = cls.now()
        return int(dt.timestamp())
    
    @classmethod
    def get_timestamp_ms(cls, dt: Optional[datetime] = None) -> int:
        """获取时间戳（毫秒）
        
        Args:
            dt: 日期时间对象，默认为当前时间
            
        Returns:
            int: 时间戳（毫秒）
        """
        if dt is None:
            dt = cls.now()
        return int(dt.timestamp() * 1000)
    
    @classmethod
    def from_timestamp(cls, timestamp: Union[int, float], tz: Optional[pytz.BaseTzInfo] = None) -> datetime:
        """从时间戳创建日期时间对象
        
        Args:
            timestamp: 时间戳（秒或毫秒）
            tz: 时区，默认为中国时区
            
        Returns:
            datetime: 日期时间对象
        """
        if tz is None:
            tz = cls.TIMEZONE_CHINA
        
        # 如果时间戳大于10位，认为是毫秒
        if timestamp > 10**10:
            timestamp = timestamp / 1000
        
        return datetime.fromtimestamp(timestamp, tz)
    
    @classmethod
    def calculate_age(cls, birth_date: Union[str, date], reference_date: Union[str, date] = None) -> int:
        """计算年龄
        
        Args:
            birth_date: 出生日期
            reference_date: 参考日期，默认为今天
            
        Returns:
            int: 年龄
        """
        if isinstance(birth_date, str):
            birth_date = cls.parse_date(birth_date)
        
        if reference_date is None:
            reference_date = cls.today()
        elif isinstance(reference_date, str):
            reference_date = cls.parse_date(reference_date)
        
        if not birth_date or not reference_date:
            raise ValueError("无效的日期")
        
        age = reference_date.year - birth_date.year
        
        # 检查是否还没到生日
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
    
    @classmethod
    def get_relative_time_description(cls, dt: datetime, reference_dt: Optional[datetime] = None) -> str:
        """获取相对时间描述
        
        Args:
            dt: 目标时间
            reference_dt: 参考时间，默认为当前时间
            
        Returns:
            str: 相对时间描述
        """
        if reference_dt is None:
            reference_dt = cls.now()
        
        # 确保两个时间都有时区信息
        if dt.tzinfo is None:
            dt = cls.TIMEZONE_CHINA.localize(dt)
        if reference_dt.tzinfo is None:
            reference_dt = cls.TIMEZONE_CHINA.localize(reference_dt)
        
        # 转换为同一时区
        dt = cls.to_china_time(dt)
        reference_dt = cls.to_china_time(reference_dt)
        
        delta = reference_dt - dt
        
        if delta.total_seconds() < 0:
            # 未来时间
            delta = -delta
            future = True
        else:
            future = False
        
        seconds = int(delta.total_seconds())
        
        if seconds < 60:
            desc = "刚刚"
        elif seconds < 3600:
            minutes = seconds // 60
            desc = f"{minutes}分钟前" if not future else f"{minutes}分钟后"
        elif seconds < 86400:
            hours = seconds // 3600
            desc = f"{hours}小时前" if not future else f"{hours}小时后"
        elif seconds < 2592000:  # 30天
            days = seconds // 86400
            desc = f"{days}天前" if not future else f"{days}天后"
        elif seconds < 31536000:  # 365天
            months = seconds // 2592000
            desc = f"{months}个月前" if not future else f"{months}个月后"
        else:
            years = seconds // 31536000
            desc = f"{years}年前" if not future else f"{years}年后"
        
        return desc


# 便捷函数
def now(tz: Optional[pytz.BaseTzInfo] = None) -> datetime:
    """获取当前时间"""
    return DateTimeUtils.now(tz)


def today(tz: Optional[pytz.BaseTzInfo] = None) -> date:
    """获取今天日期"""
    return DateTimeUtils.today(tz)


def yesterday(tz: Optional[pytz.BaseTzInfo] = None) -> date:
    """获取昨天日期"""
    return DateTimeUtils.yesterday(tz)


def parse_date(date_string: str) -> Optional[date]:
    """解析日期字符串"""
    return DateTimeUtils.parse_date(date_string)


def parse_datetime(datetime_string: str) -> Optional[datetime]:
    """解析日期时间字符串"""
    return DateTimeUtils.parse_datetime(datetime_string)


def format_date(date_obj: Union[date, datetime], format_str: str = DateTimeUtils.FORMAT_DATE) -> str:
    """格式化日期"""
    return DateTimeUtils.format_date(date_obj, format_str)


def format_datetime(datetime_obj: datetime, format_str: str = DateTimeUtils.FORMAT_DATETIME) -> str:
    """格式化日期时间"""
    return DateTimeUtils.format_datetime(datetime_obj, format_str)


def get_date_range(start_date: Union[str, date], end_date: Union[str, date]) -> List[date]:
    """获取日期范围"""
    return DateTimeUtils.get_date_range(start_date, end_date)


def get_last_n_days(n: int, end_date: Union[str, date] = None) -> List[date]:
    """获取最近N天"""
    return DateTimeUtils.get_last_n_days(n, end_date)