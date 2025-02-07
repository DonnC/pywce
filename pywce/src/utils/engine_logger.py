import logging.handlers
import os
from logging import getLogger, ERROR, DEBUG, StreamHandler
from os import getenv
from queue import Queue
from threading import Thread

from colorlog import ColoredFormatter
from pythonjsonlogger.json import JsonFormatter

# Fetch environment variables
LOGGING_ENABLED = getenv("PYWCE_LOGGER", "True").lower() == "true"
LOG_COUNT = int(getenv("PYWCE_LOG_COUNT", "3"))
LOG_SIZE = int(getenv("PYWCE_LOG_SIZE", "5"))

# Create a Queue to safely handle log messages
log_queue = Queue()

# Define file paths
log_file_path = "pywce.log"
backup_file_format = "pywce.log.{0}"


# Custom AsyncHandler to send logs to the queue
class AsyncHandler(logging.Handler):
    def emit(self, record):
        try:
            log_queue.put_nowait(self.format(record))
        except Exception:
            self.handleError(record)


# Function to handle log rotation and writing
def log_listener():
    while True:
        log_msg = log_queue.get()
        if log_msg == "exit":
            break

        # Check if the file size exceeds the limit
        if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > LOG_SIZE * 1024 * 1024:
            rotate_logs()

        # Write log message to the file
        with open(log_file_path, "a") as f:
            f.write(log_msg + "\n")


# Function to rotate log files
def rotate_logs():
    # Backup old log file by renaming
    for i in range(LOG_COUNT - 1, 0, -1):
        src = f"{log_file_path}.{i}"
        dst = f"{log_file_path}.{i + 1}"
        if os.path.exists(src):
            os.rename(src, dst)

    # Move current log file to backup
    if os.path.exists(log_file_path):
        os.rename(log_file_path, f"{log_file_path}.1")


# Start the log listener in a separate thread to prevent blocking
log_thread = Thread(target=log_listener, daemon=True)
log_thread.start()


def pywce_logger(name: str = "pywce") -> logging.Logger:
    """
    Configures and returns a logger with both console and file logging, using queue-based async logging.
    Includes manual log file rotation.
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

    file_formatter = JsonFormatter(
        '%(asctime)s [%(levelname)s] [%(name)s] - {%(filename)s:%(lineno)d} %(funcName)s - %(message)s'
    )

    # Console handler for immediate output
    stream_handler = StreamHandler()
    stream_handler.setLevel(DEBUG)
    stream_handler.setFormatter(console_formatter)
    logger.addHandler(stream_handler)

    # Async-safe file handler for logging (using QueueHandler)
    async_file_handler = AsyncHandler()
    async_file_handler.setLevel(DEBUG)
    async_file_handler.setFormatter(file_formatter)
    logger.addHandler(async_file_handler)

    return logger
