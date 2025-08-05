from .init_db import db_client
from ..schemas import OauthInfoTable
from ..logger import create_logger
from sqlalchemy import select

logger = create_logger(__name__)

def query_oauth_by_controler_id(controler_id:str,channel:str):
    with db_client.session_scope as session:
        stmt = select(OauthInfoTable).where((OauthInfoTable.controler_id == controler_id) & (OauthInfoTable.channel == channel))
        oauth_info = session.execute(stmt).scalar_one_or_none()
        logger.info('query_oauth_by_controler_id return success!')
        logger.debug(f'query_oauth_by_controler_id,controler_id:{controler_id},channel:{channel},oauth_info:{oauth_info}')
        return oauth_info


def query_oauth_by_controler_name(controler_name:str,channel:str):
    with db_client.session_scope as session:
        stmt = select(OauthInfoTable).where((OauthInfoTable.controler_name == controler_name) & (OauthInfoTable.channel == channel))
        oauth_info = session.execute(stmt).scalar_one_or_none()
        logger.info('query_oauth_by_controler_name return success!')
        logger.debug(f'query_oauth_by_controler_name,controler_name:{controler_name},channel:{channel},oauth_info:{oauth_info}')
        return oauth_info
    
def update_oauth_info(controler_id:str,controler_name:str,channel:str,oauth_info:dict):
    logger.info('update_oauth_info start!')
    logger.debug(f'update_oauth_info,controler_id:{controler_id},controler_name:{controler_name},channel:{channel},oauth_info:{oauth_info}')
    with db_client.session_scope as session:
        stmt = select(OauthInfoTable).where((OauthInfoTable.controler_id == controler_id) & (OauthInfoTable.channel == channel))
        db_oauth_info = session.execute(stmt).scalar_one_or_none()
        if db_oauth_info:
            db_oauth_info.oauth_info = oauth_info
            logger.info('update_oauth_info update success!')
            logger.debug(f'update_oauth_info,controler_id:{controler_id},controler_name:{controler_name},channel:{channel},oauth_info:{oauth_info}')
            return f"controler_id:{controler_id},controler_name:{controler_name} is update"
        else:
            oauth_info = OauthInfoTable(controler_id=controler_id,controler_name=controler_name,channel=channel,oauth_info=oauth_info)
            session.add(oauth_info)
            logger.info('update_oauth_info insert success!')
            logger.debug(f'update_oauth_info,controler_id:{controler_id},controler_name:{controler_name},channel:{channel},oauth_info:{oauth_info}')
            return f"controler_id:{controler_id},controler_name:{controler_name} is insert"

