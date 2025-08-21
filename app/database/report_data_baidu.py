from .init_db import db_client
from .schemas import OdsAdsBaiduKeywordDaily,OdsAdsBaiduKeywordHour

from ..logger import create_logger,logger_wrapper
from sqlalchemy import insert,Result
from typing import Generator

logger = create_logger(__name__)


def insert_baidu_keyword_daily(data:Generator[dict,None,None]):
    stmt = insert(OdsAdsBaiduKeywordDaily)
    try:
        with db_client.session_scope as session:
            session.execute(stmt,data)
        logger.info_database("OdsAdsBaiduKeywordDaily insert success")
        return True
    except Exception as e:
        logger.error(f"OdsAdsBaiduKeywordDaily insert error {e}")
        return False



def insert_baidu_keyword_hour(data:Generator[dict,None,None]):
    stmt = insert(OdsAdsBaiduKeywordHour)
    try:
        with db_client.session_scope as session:
            session.execute(stmt,data)
        logger.info_database("OdsAdsBaiduKeywordHour insert success")
        return True
    except Exception as e:
        logger.error(f"OdsAdsBaiduKeywordHour insert error {e}")
        return False
