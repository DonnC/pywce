import logging
from os import getenv

# env log properties
_LOGGING_ENABLED = int(getenv("PYWCE_LOGGER", "1")) == 1


def pywce_logger(name: str = "pywce", file: bool = False) -> logging.Logger:
    """
    Configures and returns a logger with both console and file logging.
    """
    logger = logging.getLogger(name)

    if not _LOGGING_ENABLED:
        logger.setLevel(logging.ERROR)
        return logger

    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_formatter = logging.Formatter(
        '%(log_color)s%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(console_formatter)
    logger.addHandler(stream_handler)

    return logger
