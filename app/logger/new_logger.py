from tk_base_utils.tk_logger import get_logger,logger_wrapper,set_logger_config_path
from tk_base_utils import find_file

config_path = find_file('config.toml')
set_logger_config_path(config_path)
def create_logger(name:str|None=None):
    logger = get_logger()
    return logger

