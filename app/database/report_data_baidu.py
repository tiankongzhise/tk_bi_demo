from .init_db import db_client
from .schemas import OdsAdsBaiduKeywordDaily
from ..logger import create_logger,logger_wrapper
from sqlalchemy import insert,Result
from typing import Generator

logger = create_logger(__name__)


def insert_baidu_keyword_daily(data:Generator[dict,None,None]):
    stmt = insert(OdsAdsBaiduKeywordDaily)
    try:
        with db_client.session_scope as session:
            session.execute(stmt,data)
        logger.info("OdsAdsBaiduKeywordDaily insert success")
        return True
    except Exception as e:
        logger.error(f"OdsAdsBaiduKeywordDaily insert error {e}")
        return False



