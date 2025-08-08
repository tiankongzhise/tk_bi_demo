from tk_db_utils import get_db_client,SqlAlChemyBase,set_db_config_path
from tk_base_utils import get_target_file_path
from ..logger import create_logger

logger = create_logger(__name__)
    
    
def init_db_client():
    logger.info('init_db_client!')
    env_file_path = get_target_file_path('.env')
    db_config_path = get_target_file_path('config.toml')
    set_db_config_path(db_config_path,env_file_path)
    db_client = get_db_client()
    logger.info('init_db_client success!')
    return db_client


db_client = init_db_client()
