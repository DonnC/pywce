import logging
from os import getenv

def pywce_logger(name: str = "pywce", file: bool = False) -> logging.Logger:
    """
    Configures and returns a logger with both console and file logging.
    """
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        console_formatter = logging.Formatter(
            '%(log_color)s%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(console_formatter)
        logger.addHandler(stream_handler)

    log_level = getenv("PYWCE_LOG_LEVEL", "DEBUG").upper()
    logger.setLevel(getattr(logging, log_level, logging.DEBUG))

    return logger
