from tk_db_utils import get_db_client
from tk_base_utils import find_file
from src.t1.sec import BaseTableEnhanced
from src.t1.sec import AdGroupSnapshot, CampaignSnapshot,KeywordSnapshot,CreativeSnapshot
from sqlalchemy import select,and_,between
from datetime import datetime

def init_db():
    env_path = find_file(".env")
    db_config_path = find_file("config.toml")
    db_client = get_db_client(env_path, db_config_path,db_config_path)
    return db_client

def drop_db():
    db_client = init_db()
    # BaseTableEnhanced.metadata.drop_all(db_client.engine)
    CreativeSnapshot.__table__.drop(db_client.engine)
    KeywordSnapshot.__table__.drop(db_client.engine)
    AdGroupSnapshot.__table__.drop(db_client.engine)
    CampaignSnapshot.__table__.drop(db_client.engine)

def query_test_data():
    db_client = init_db()
    with db_client.session_scope as session:
        # 需要通过外键联查出计划单元名称
        stmt = select(KeywordSnapshot, AdGroupSnapshot.adgroup_name, CampaignSnapshot.campaign_name).where(
            KeywordSnapshot.expiry_date == datetime(9999, 12, 31, 23, 59, 59)
        )
        stmt = stmt.join(AdGroupSnapshot, and_(
            KeywordSnapshot.adgroup_id == AdGroupSnapshot.adgroup_id,
            KeywordSnapshot.user_id == AdGroupSnapshot.user_id,
            between(KeywordSnapshot.effective_date, AdGroupSnapshot.effective_date,AdGroupSnapshot.expiry_date)
        ))
        stmt = stmt.join(CampaignSnapshot, and_(
            AdGroupSnapshot.campaign_id == CampaignSnapshot.campaign_id,
            AdGroupSnapshot.user_id == CampaignSnapshot.user_id,
            between(KeywordSnapshot.effective_date, CampaignSnapshot.effective_date,CampaignSnapshot.expiry_date)
        ))
        result = session.execute(stmt).all()
        for row in result:
            creative, adgroup_name, campaign_name = row
            print(f"创意: {creative.to_dict()}, 单元名称: {adgroup_name}, 计划名称: {campaign_name}")
        
if __name__ == "__main__":
    # db_client = init_db()
    # is_clean = input("是否清理数据库(y/n)\n")
    # if is_clean == "y":
    #     drop_db()
    # init_db()
    query_test_data()
    # drop_db()
