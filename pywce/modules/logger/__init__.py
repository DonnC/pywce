import logging
from abc import ABC, abstractmethod
from typing import Any


class PywceLogger(ABC):
    """Abstract logger interface for Pywce. Clients can extend this to configure their own logging."""

    @abstractmethod
    def log(self, message: Any, level: str = "INFO"):
        """Logs a message at the given level."""
        pass


class DefaultPywceLogger(PywceLogger):
    """Default logger implementation with support for logging and print statements."""

    def __init__(self, use_print: bool = False):
        self.use_print = use_print
        self.logger = logging.getLogger("pywce")

        if not self.logger.hasHandlers():
            console_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(console_formatter)
            self.logger.addHandler(stream_handler)

        self.logger.setLevel(logging.DEBUG)

    def log(self, message: str, level: str = "INFO"):
        if self.use_print:
            print(f"[{level}] {message}")
        else:
            getattr(self.logger, level.lower())(message)
