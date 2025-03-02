from logging import StreamHandler, getLogger, ERROR, Logger, DEBUG
from logging.handlers import RotatingFileHandler
from os import getenv

from colorlog import ColoredFormatter
from pythonjsonlogger import json

# env log properties
LOGGING_ENABLED = int(getenv("PYWCE_LOGGER", "1")) == 1
LOG_COUNT = int(getenv("PYWCE_LOG_COUNT", "3"))
LOG_SIZE = int(getenv("PYWCE_LOG_SIZE", "5"))

def pywce_logger(name: str = "pywce", file: bool =True) -> Logger:
    """
    Configures and returns a logger with both console and file logging.
    """
    logger = getLogger(name)

    # Log file configuration
    max_log_size = LOG_SIZE * 1024 * 1024

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

    stream_handler = StreamHandler()
    stream_handler.setLevel(DEBUG)
    stream_handler.setFormatter(console_formatter)
    logger.addHandler(stream_handler)

    if file is True:
        file_formatter = json.JsonFormatter(
            '%(asctime)s [%(levelname)s] [%(name)s] - {%(filename)s:%(lineno)d} %(funcName)s - %(message)s'
        )

        file_handler = RotatingFileHandler("pywce.log", maxBytes=max_log_size, backupCount=LOG_COUNT)
        file_handler.setLevel(DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
