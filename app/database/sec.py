from tk_db_utils import DbOrmBaseMixedIn
from sqlalchemy import DateTime, Integer, BigInteger, VARCHAR, DECIMAL, JSON, UniqueConstraint, Index, ForeignKeyConstraint,TEXT
from sqlalchemy.orm import mapped_column, declared_attr, Mapped,relationship
from datetime import datetime
from copy import deepcopy

class BaseTableEnhanced(DbOrmBaseMixedIn):
    __abstract__ = True
    
    # 定义schema名称，子类可以覆盖
    _schema_name = "test_db"
    
    @classmethod
    def get_full_table_name(cls, table_name):
        """获取完整的表名（包含schema）"""
        return f"{cls._schema_name}.{table_name}"
    def _add_default_schema(cls):
        """添加默认schema"""
        if hasattr(cls, '__table_args__'):
            original_table_args = deepcopy(cls.__table_args__)
            new_table_args = []
            schema_status = True
            for item in original_table_args:
                if isinstance(item, dict):
                    if 'schema' in item:
                        schema_status = False
                new_table_args.append(item)
            if schema_status:
                new_table_args.append({'schema':BaseTableEnhanced._schema_name})
            cls.__table_args__ = tuple(new_table_args)
        else:
            cls.__table_args__ = (
                {'schema':BaseTableEnhanced._schema_name},
            )

    def __init_subclass__(cls, **kwargs):
        cls._add_default_schema(cls)
        super().__init_subclass__(**kwargs)

    


    @declared_attr
    def create_at(cls):
        return mapped_column(DateTime, default=datetime.now)
    
    @declared_attr
    def update_at(cls):
        return mapped_column(DateTime, nullable=True, onupdate=datetime.now)


class CampaignSnapshot(BaseTableEnhanced):
    __tablename__ = "campaign_snapshot"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 业务主键
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    user_id: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, comment="账户ID")
    
    # 拉链表字段
    effective_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="生效日期")
    expiry_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime(9999, 12, 31,23,59,59), comment="失效日期")
    
    # 业务字段
    campaign_name: Mapped[str] = mapped_column(VARCHAR(200), comment="推广计划名称")
    status: Mapped[int] = mapped_column(Integer, comment="状态")
    budget: Mapped[float] = mapped_column(DECIMAL(15, 2), comment="预算")
    data_json: Mapped[dict] = mapped_column(JSON, comment="完整数据JSON")
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", "effective_date", name="uix_campaign_snapshot_key"),
        Index("idx_campaign_current", "campaign_id", "user_id", "expiry_date"),
        Index("idx_campaign_user_date", "user_id", "effective_date"),
        # {'schema':BaseTableEnhanced._schema_name}
    )


class AdGroupSnapshot(BaseTableEnhanced):
    __tablename__ = "adgroup_snapshot"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 业务主键
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    user_id: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, comment="账户ID")
    
    # 拉链表字段
    effective_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="生效日期")
    expiry_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime(9999, 12, 31,23,59,59), comment="失效日期")
    
    # 业务字段
    adgroup_name: Mapped[str] = mapped_column(VARCHAR(200), comment="推广单元名称")
    
    # 外键关系
    campaign: Mapped["CampaignSnapshot"] = relationship(
        "CampaignSnapshot",
        foreign_keys=[campaign_id],
        primaryjoin="and_(AdGroupSnapshot.campaign_id == CampaignSnapshot.campaign_id, "
                   "AdGroupSnapshot.user_id == CampaignSnapshot.user_id)",
        viewonly=True
    )
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint("adgroup_id", "user_id", "effective_date", name="uix_adgroup_snapshot_key"),
        Index("idx_adgroup_current", "adgroup_id", "user_id", "expiry_date"),
        Index("idx_adgroup_campaign", "campaign_id", "user_id", "expiry_date"),
        ForeignKeyConstraint(
            ["campaign_id", "user_id"],
            [f"{BaseTableEnhanced._schema_name}.campaign_snapshot.campaign_id", f"{BaseTableEnhanced._schema_name}.campaign_snapshot.user_id"],
            name="fk_adgroup_campaign"
        ),
        # {'schema':BaseTableEnhanced._schema_name}
    )


class KeywordSnapshot(BaseTableEnhanced):
    __tablename__ = "keyword_snapshot"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 业务主键
    keyword_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关键词ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    user_id: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, comment="账户ID")
    
    # 拉链表字段
    effective_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="生效日期")
    expiry_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime(9999, 12, 31,23,59,59), comment="失效日期")
    
    # 业务字段
    keyword_text: Mapped[str] = mapped_column(VARCHAR(500), comment="关键词文本")

    
    # 外键关系
    adgroup: Mapped["AdGroupSnapshot"] = relationship(
        "AdGroupSnapshot",
        foreign_keys=[adgroup_id],
        primaryjoin="and_(KeywordSnapshot.adgroup_id == AdGroupSnapshot.adgroup_id, "
                   "KeywordSnapshot.user_id == AdGroupSnapshot.user_id)",
        viewonly=True
    )
    
    # campaign: Mapped["CampaignSnapshot"] = relationship(
    #     "CampaignSnapshot",
    #     foreign_keys=[campaign_id],
    #     primaryjoin="and_(KeywordSnapshot.campaign_id == CampaignSnapshot.campaign_id, "
    #                "KeywordSnapshot.user_id == CampaignSnapshot.user_id, "
    #                "CampaignSnapshot.expiry_date == date(9999, 12, 31))",
    #     viewonly=True
    # )
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint("keyword_id", "user_id", "effective_date", name="uix_keyword_snapshot_key"),
        Index("idx_keyword_current", "keyword_id", "user_id", "expiry_date"),
        Index("idx_keyword_adgroup", "adgroup_id", "user_id", "expiry_date"),
        ForeignKeyConstraint(
            ["adgroup_id", "user_id"],
            [f"{BaseTableEnhanced._schema_name}.adgroup_snapshot.adgroup_id", f"{BaseTableEnhanced._schema_name}.adgroup_snapshot.user_id"],
            name="fk_keyword_adgroup"
        ),
        # ForeignKeyConstraint(
        #     ["campaign_id", "user_id"],
        #     [f"{BaseTableEnhanced._schema_name}.campaign_snapshot.campaign_id", f"{BaseTableEnhanced._schema_name}.campaign_snapshot.user_id"],
        #     name="fk_keyword_campaign"
        # ),
        # {'schema':BaseTableEnhanced._schema_name}
    )


class CreativeSnapshot(BaseTableEnhanced):
    __tablename__ = "creative_snapshot"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 业务主键
    creative_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创意ID")
    adgroup_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广单元ID")
    campaign_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="推广计划ID")
    user_id: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, comment="账户ID")
    
    # 拉链表字段
    effective_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="生效日期")
    expiry_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime(9999, 12, 31,23,59,59), comment="失效日期")
    
    # 业务字段
    title: Mapped[str] = mapped_column(VARCHAR(500), comment="创意标题")
    description1: Mapped[str] = mapped_column(TEXT, comment="创意描述1")
    description2: Mapped[str] = mapped_column(TEXT, comment="创意描述2")
    
    # 外键关系
    adgroup: Mapped["AdGroupSnapshot"] = relationship(
        "AdGroupSnapshot",
        foreign_keys=[adgroup_id],
        primaryjoin="and_(CreativeSnapshot.adgroup_id == AdGroupSnapshot.adgroup_id, "
                   "CreativeSnapshot.user_id == AdGroupSnapshot.user_id)",
        viewonly=True
    )
    
    # campaign: Mapped["CampaignSnapshot"] = relationship(
    #     "CampaignSnapshot",
    #     foreign_keys=[campaign_id],
    #     primaryjoin="and_(CreativeSnapshot.campaign_id == CampaignSnapshot.campaign_id, "
    #                "CreativeSnapshot.user_id == CampaignSnapshot.user_id, "
    #                "CampaignSnapshot.expiry_date == date(9999, 12, 31))",
    #     viewonly=True
    # )
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint("creative_id", "user_id", "effective_date", name="uix_creative_snapshot_key"),
        Index("idx_creative_current", "creative_id", "user_id", "expiry_date"),
        Index("idx_creative_adgroup", "adgroup_id", "user_id", "expiry_date"),
        ForeignKeyConstraint(
            ["adgroup_id", "user_id"],
            [f"{BaseTableEnhanced._schema_name}.adgroup_snapshot.adgroup_id", f"{BaseTableEnhanced._schema_name}.adgroup_snapshot.user_id"],
            name="fk_creative_adgroup"
        ),
        # ForeignKeyConstraint(
        #     ["campaign_id", "user_id"],
        #     [f"{BaseTableEnhanced._schema_name}.campaign_snapshot.campaign_id", f"{BaseTableEnhanced._schema_name}.campaign_snapshot.user_id"],
        #     name="fk_creative_campaign"
        # ),
        # {'schema':BaseTableEnhanced._schema_name}
    )
