import logging

from rich.logging import RichHandler


def setup_logger():
    logger = logging.getLogger("pywce")
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()

    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_level=True,
        markup=True,
        log_time_format="[%Y-%m-%d %H:%M:%S]"
    )
    rich_handler.setLevel(logging.INFO)

    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)] %(message)s",
        '%Y-%m-%d %H:%M:%S',
    )
    rich_handler.setFormatter(console_formatter)
    logger.addHandler(rich_handler)

    fh = logging.FileHandler("pywce.log")
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
        "%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    return logger
