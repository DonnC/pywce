from logging import StreamHandler, getLogger, ERROR, Logger, DEBUG
from logging.handlers import RotatingFileHandler
from os import getenv

from colorlog import ColoredFormatter
from pythonjsonlogger import json

# Default logging enabled flag (you can change this to False for disabling)
LOGGING_ENABLED = getenv("PYWCE_LOGGER_ENABLED", "True").lower() == "true"

# Log file configuration
LOG_FILE = "pywce.log"
MAX_LOG_SIZE = 5 * 1024 * 1024
BACKUP_COUNT = 5


def _get_logger(name: str = None) -> Logger:
    """
    Configures and returns a logger with both console and file logging.
    """
    logger = getLogger(name)

    if not LOGGING_ENABLED:
        logger.setLevel(ERROR)
        return logger

    logger.setLevel(DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_formatter = ColoredFormatter(
        '%(log_color)s%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'green',
            'INFO': 'blue',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red'
        }
    )

    file_formatter = json.JsonFormatter(
        '%(asctime)s [%(levelname)s] [%(name)s] - {%(filename)s:%(lineno)d} %(funcName)s - %(message)s'
    )

    stream_handler = StreamHandler()
    stream_handler.setLevel(DEBUG)
    stream_handler.setFormatter(console_formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
    file_handler.setLevel(DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_engine_logger(name: str = "pywce"):
    return _get_logger(name)
