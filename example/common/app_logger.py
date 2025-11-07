import logging

from rich.logging import RichHandler

log_level = logging.DEBUG


def setup_logger():
    logger = logging.getLogger("pywce")
    logger.setLevel(log_level)

    logger.handlers.clear()

    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_level=True,
        markup=True,
        log_time_format="[%Y-%m-%d %H:%M:%S]"
    )
    rich_handler.setLevel(log_level)

    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        '%Y-%m-%d %H:%M:%S',
    )
    rich_handler.setFormatter(console_formatter)
    logger.addHandler(rich_handler)

    fh = logging.FileHandler("pywce.log")
    fh.setLevel(log_level)
    fh_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
        "%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    return logger
