import logging 
from tk_base_utils import load_toml
import os

logger_center = {}


def get_level_mapping():
    level_mapping = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    return level_mapping


def set_logger():
    config = load_toml("config.toml")
    # Ensure the log directory exists
    log_dir = os.path.dirname(config["log"]["path"])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    level_mapping = get_level_mapping()
    
    logging.basicConfig(
        level=level_mapping[config["log"]["level"]],
        format=config["log"]["format"],
        handlers=[
            logging.FileHandler(config["log"]["path"])
        ]
        )

# def reload_logger_level(logger: logging.Logger):
#     config = load_toml("config.toml")
#     level_mapping = get_level_mapping()
#     logger_level = level_mapping[config["log"]["level"]]
#     for logger_name,logger in logger_center.items():
#         logger.setLevel(logger_level)
#         logger.warning(f"{logger_name} 日志级别已更改为: {logger_level}")

def reload_logger_level(logger: logging.Logger):
    config = load_toml("config.toml")
    level_mapping = get_level_mapping()
    logger_level = level_mapping[config["log"]["level"]]
    
    # 更新root logger级别
    logging.getLogger().setLevel(logger_level)
    
    # 更新所有handler级别
    for handler in logging.getLogger().handlers:
        handler.setLevel(logger_level)
    
    # 更新注册的logger级别
    for logger_name, logger in logger_center.items():
        logger.setLevel(logger_level)
        logger.warning(f"{logger_name} 日志级别已更改为: {logger_level}")

def set_logger_name(name: str):
    logging.getLogger(name)

def create_logger(name: str):
    set_logger()
    logger = logging.getLogger(name)
    register_logger(logger)
    return logger

def register_logger(logger: logging.Logger):
    logger_center[logger.name] = logger
    
    
