from tk_db_utils import DbOrmBaseMixedIn
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import Integer, JSON, VARCHAR, UniqueConstraint, DateTime, Index, BigInteger, Date, Boolean, Text
from datetime import datetime


class BaseZipperTable(DbOrmBaseMixedIn):
    """拉链表基类，包含拉链表通用字段"""
    __abstract__ = True

    @declared_attr
    def create_at(cls):
        return mapped_column(DateTime, default=datetime.now)
    
    @declared_attr
    def update_at(cls):
        return mapped_column(DateTime, nullable=True, onupdate=datetime.now)
    
    # 拉链表核心字段
    effective_start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="有效开始时间")
    effective_end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="有效结束时间，NULL表示当前有效")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否为当前有效记录")
    data_version: Mapped[int] = mapped_column(Integer, default=1, comment="数据版本号")
    change_type: Mapped[str] = mapped_column(VARCHAR(10), comment="变更类型：INSERT/UPDATE/DELETE")


class BaiduCampaignZipper(BaseZipperTable):
    """百度推广计划拉链表"""
    __tablename__ = "baidu_campaign_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户名称")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    campaign_name: Mapped[str] = mapped_column(VARCHAR(255), comment="推广计划名称")
    
    # 推广计划基本信息
    status: Mapped[str] = mapped_column(VARCHAR(20), comment="推广计划状态")
    budget: Mapped[str] = mapped_column(VARCHAR(50), comment="预算")
    schedule: Mapped[dict] = mapped_column(JSON, comment="投放时间段")
    target_setting: Mapped[dict] = mapped_column(JSON, comment="定向设置")
    
    # 完整的原始数据
    raw_data: Mapped[dict] = mapped_column(JSON, comment="完整的原始数据")
    
    __table_args__ = (
        UniqueConstraint("user_name", "campaign_id", "effective_start_date", name="uix_campaign_zipper_unique"),
        Index("idx_campaign_current", "user_name", "campaign_id", "is_current"),
        Index("idx_campaign_effective_date", "effective_start_date", "effective_end_date"),
        {"schema": "ods_ads"},
    )


class BaiduAdgroupZipper(BaseZipperTable):
    """百度推广单元拉链表"""
    __tablename__ = "baidu_adgroup_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户名称")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    adgroup_name: Mapped[str] = mapped_column(VARCHAR(255), comment="推广单元名称")
    
    # 推广单元基本信息
    status: Mapped[str] = mapped_column(VARCHAR(20), comment="推广单元状态")
    max_price: Mapped[str] = mapped_column(VARCHAR(50), comment="单元出价")
    negative_words: Mapped[dict] = mapped_column(JSON, comment="否定关键词")
    exact_negative_words: Mapped[dict] = mapped_column(JSON, comment="精确否定关键词")
    
    # 完整的原始数据
    raw_data: Mapped[dict] = mapped_column(JSON, comment="完整的原始数据")
    
    __table_args__ = (
        UniqueConstraint("user_name", "campaign_id", "adgroup_id", "effective_start_date", name="uix_adgroup_zipper_unique"),
        Index("idx_adgroup_current", "user_name", "campaign_id", "adgroup_id", "is_current"),
        Index("idx_adgroup_effective_date", "effective_start_date", "effective_end_date"),
        {"schema": "ods_ads"},
    )


class BaiduKeywordZipper(BaseZipperTable):
    """百度关键词拉链表（包含autoExpansion数据）"""
    __tablename__ = "baidu_keyword_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户名称")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    keyword_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关键词ID")
    keyword_text: Mapped[str] = mapped_column(VARCHAR(500), comment="关键词文本")
    
    # 关键词基本信息
    status: Mapped[str] = mapped_column(VARCHAR(20), comment="关键词状态")
    match_type: Mapped[str] = mapped_column(VARCHAR(20), comment="匹配方式")
    price: Mapped[str] = mapped_column(VARCHAR(50), comment="出价")
    destination_url: Mapped[str] = mapped_column(Text, comment="访问URL")
    
    # 标识是否为autoExpansion数据
    is_auto_expansion: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为自动扩展关键词")
    
    # 完整的原始数据
    raw_data: Mapped[dict] = mapped_column(JSON, comment="完整的原始数据")
    
    __table_args__ = (
        UniqueConstraint("user_name", "campaign_id", "adgroup_id", "keyword_id", "effective_start_date", name="uix_keyword_zipper_unique"),
        Index("idx_keyword_current", "user_name", "campaign_id", "adgroup_id", "keyword_id", "is_current"),
        Index("idx_keyword_effective_date", "effective_start_date", "effective_end_date"),
        Index("idx_keyword_auto_expansion", "is_auto_expansion"),
        {"schema": "ods_ads"},
    )


class BaiduCreativeZipper(BaseZipperTable):
    """百度创意拉链表"""
    __tablename__ = "baidu_creative_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户名称")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    creative_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创意ID")
    
    # 创意基本信息
    title: Mapped[str] = mapped_column(VARCHAR(500), comment="创意标题")
    description1: Mapped[str] = mapped_column(VARCHAR(500), comment="创意描述1")
    description2: Mapped[str] = mapped_column(VARCHAR(500), comment="创意描述2")
    destination_url: Mapped[str] = mapped_column(Text, comment="访问URL")
    display_url: Mapped[str] = mapped_column(VARCHAR(500), comment="显示URL")
    status: Mapped[str] = mapped_column(VARCHAR(20), comment="创意状态")
    
    # 完整的原始数据
    raw_data: Mapped[dict] = mapped_column(JSON, comment="完整的原始数据")
    
    __table_args__ = (
        UniqueConstraint("user_name", "campaign_id", "adgroup_id", "creative_id", "effective_start_date", name="uix_creative_zipper_unique"),
        Index("idx_creative_current", "user_name", "campaign_id", "adgroup_id", "creative_id", "is_current"),
        Index("idx_creative_effective_date", "effective_start_date", "effective_end_date"),
        {"schema": "ods_ads"},
    )