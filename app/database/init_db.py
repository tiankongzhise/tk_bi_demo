from tk_db_utils import get_db_client,SqlAlChemyBase
from tk_base_utils import get_target_file_path
from ..logger import create_logger

logger = create_logger(__name__)
    
    
def init_db_client():
    logger.info('init_db_client!')
    env_file_path = get_target_file_path('.env')
    db_config_path = get_target_file_path('config.toml')
    db_client = get_db_client()
    db_client = db_client.auto_init(env_file_path,db_config_path,SqlAlChemyBase)
    logger.info('init_db_client success!')
    return db_client


db_client = init_db_client()
