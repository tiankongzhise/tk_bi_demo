from sqlalchemy.schema import ForeignKey
from tk_db_utils import DbOrmBaseMixedIn
from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship
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
    """百度推广计划拉链表 - 账户结构层级"""
    __tablename__ = "baidu_campaign_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    
    # 推广计划结构字段
    campaign_name: Mapped[str] = mapped_column(VARCHAR(255), comment="推广计划名称")
    
    # 反向关系定义
    adgroups = relationship("BaiduAdgroupZipper", back_populates="campaign")
    keywords = relationship("BaiduKeywordZipper", back_populates="campaign")
    creatives = relationship("BaiduCreativeZipper", back_populates="campaign")
    
    __table_args__ = (
        UniqueConstraint("user_id", "campaign_id", "effective_start_date", name="uix_campaign_zipper_unique"),
        Index("idx_campaign_current", "user_id", "campaign_id", "is_current"),
        Index("idx_campaign_effective_date", "effective_start_date", "effective_end_date"),
        Index("idx_campaign_id", "campaign_id"),  # 为外键约束添加索引
        {"schema": "ods_ads"},
    )


class BaiduAdgroupZipper(BaseZipperTable):
    """百度推广单元拉链表 - 账户结构层级"""
    __tablename__ = "baidu_adgroup_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ods_ads.baidu_campaign_zipper.campaign_id"), nullable=False, comment="推广计划ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    
    # 推广单元结构字段
    adgroup_name: Mapped[str] = mapped_column(VARCHAR(255), comment="推广单元名称")
    
    # 关系定义
    campaign = relationship("BaiduCampaignZipper", back_populates="adgroups")
    keywords = relationship("BaiduKeywordZipper", back_populates="adgroup")
    creatives = relationship("BaiduCreativeZipper", back_populates="adgroup")
    
    __table_args__ = (
        UniqueConstraint("user_id", "campaign_id", "adgroup_id", "effective_start_date", name="uix_adgroup_zipper_unique"),
        Index("idx_adgroup_current", "user_id", "campaign_id", "adgroup_id", "is_current"),
        Index("idx_adgroup_effective_date", "effective_start_date", "effective_end_date"),
        Index("idx_adgroup_id", "adgroup_id"),  # 为外键约束添加索引
        {"schema": "ods_ads"},
    )


class BaiduKeywordZipper(BaseZipperTable):
    """百度关键词拉链表 - 账户结构层级（包含autoExpansion数据）"""
    __tablename__ = "baidu_keyword_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ods_ads.baidu_campaign_zipper.campaign_id"), nullable=False, comment="推广计划ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ods_ads.baidu_adgroup_zipper.adgroup_id"), nullable=False, comment="推广单元ID")
    keyword_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关键词ID")
    
    # 关键词结构字段
    keyword_text: Mapped[str] = mapped_column(VARCHAR(500), comment="关键词文本")
    
    # 标识是否为autoExpansion数据
    is_auto_expansion: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为自动扩展关键词")
    
    # 关系定义
    campaign = relationship("BaiduCampaignZipper", back_populates="keywords")
    adgroup = relationship("BaiduAdgroupZipper", back_populates="keywords")
    
    __table_args__ = (
        UniqueConstraint("user_id", "campaign_id", "adgroup_id", "keyword_id", "effective_start_date", name="uix_keyword_zipper_unique"),
        Index("idx_keyword_current", "user_id", "campaign_id", "adgroup_id", "keyword_id", "is_current"),
        Index("idx_keyword_effective_date", "user_id", "effective_start_date", "effective_end_date"),
        Index("idx_keyword_auto_expansion", "user_id", "is_auto_expansion"),
        {"schema": "ods_ads"},
    )


class BaiduCreativeZipper(BaseZipperTable):
    """百度创意拉链表 - 账户结构层级"""
    __tablename__ = "baidu_creative_zipper"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, comment="账户ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ods_ads.baidu_campaign_zipper.campaign_id"), nullable=False, comment="推广计划ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ods_ads.baidu_adgroup_zipper.adgroup_id"), nullable=False, comment="推广单元ID")
    creative_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创意ID")
    
    # 创意结构字段
    title: Mapped[str] = mapped_column(VARCHAR(500), comment="创意标题")
    description1: Mapped[str] = mapped_column(VARCHAR(500), comment="创意描述1")
    description2: Mapped[str] = mapped_column(VARCHAR(500), comment="创意描述2")
    
    # 关系定义
    campaign = relationship("BaiduCampaignZipper", back_populates="creatives")
    adgroup = relationship("BaiduAdgroupZipper", back_populates="creatives")

    __table_args__ = (
        UniqueConstraint("user_id", "campaign_id", "adgroup_id", "creative_id", "effective_start_date", name="uix_creative_zipper_unique"),
        Index("idx_creative_current", "user_id", "campaign_id", "adgroup_id", "creative_id", "is_current"),
        Index("idx_creative_effective_date", "user_id", "effective_start_date", "effective_end_date"),
        {"schema": "ods_ads"},
    )
