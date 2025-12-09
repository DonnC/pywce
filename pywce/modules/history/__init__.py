import datetime
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Any

from pydantic import BaseModel

_logger = logging.getLogger(__name__)


class History(BaseModel):
    role: str
    uid: str
    message_type: str
    timestamp: str
    content: Optional[str] = None
    stage: Optional[str] = None
    metadata: Optional[Any] = None


class IHistoryManager(ABC):
    """
        A history interface to log every message interaction between users and bot
    """

    @abstractmethod
    def log_message(self, message: History):
        """Append a message to the history log."""
        pass

    @abstractmethod
    def get_history(self, uid: Optional[str] = None, limit: int = 50) -> List[History]:
        """Retrieve recent history (optional implementation)."""
        pass


class FileHistoryManager(IHistoryManager):
    # 5 MB in bytes
    _MAX_SIZE = 5 * 1024 * 1024

    def __init__(self, base_dir: str = "pywce_history", file_max_size: Optional[int] = None):
        self.base_dir = base_dir
        self.file_max_size = file_max_size or self._MAX_SIZE
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            _logger.debug("Saving chat history to dir: %s", self.base_dir)

    def _get_base_file_path(self) -> str:
        """Returns the path for the current, non-rotated file (e.g., 2025-12-09.jsonl)."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"{today}.jsonl"
        return os.path.join(self.base_dir, filename)

    def _rotate_file(self, file_path: str):
        """
        Checks file size and rotates if file_max_size is exceeded.
        Renames file.jsonl to file.0.jsonl, file.1.jsonl, etc.
        """
        if not os.path.exists(file_path):
            return

        # Check if rotation is necessary
        if os.path.getsize(file_path) > self.file_max_size:
            _logger.info("Log file exceeded %s MB. Initiating rotation for %s", self.file_max_size / (1024 * 1024),
                         file_path)

            base_name = os.path.basename(file_path)
            # e.g., '2025-12-09.jsonl' -> '2025-12-09' and '.jsonl'
            name_part, ext_part = os.path.splitext(base_name)

            # Find the highest existing rotation number
            max_rotation = -1
            for filename in os.listdir(self.base_dir):
                if filename.startswith(name_part) and filename.endswith(ext_part):
                    parts = filename.split('.')
                    # Expects format like 'YYYY-MM-DD.N.jsonl'
                    if len(parts) == 3 and parts[1].isdigit():
                        max_rotation = max(max_rotation, int(parts[1]))

            next_rotation = max_rotation + 1

            # Create the new rotated file name (e.g., 2025-12-09.0.jsonl)
            rotated_file_name = f"{name_part}.{next_rotation}{ext_part}"
            rotated_path = os.path.join(self.base_dir, rotated_file_name)

            # Rename the current active file
            os.rename(file_path, rotated_path)
            _logger.info("File rotated successfully to %s", rotated_path)

    def log_message(self, message: History):
        file_path = self._get_base_file_path()

        # 1. Pre-check rotation before writing
        # This prevents the file from becoming huge before the next write.
        self._rotate_file(file_path)

        # 2. Log the message to the (potentially newly created) base file
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(message.model_dump_json() + "\n")
        except Exception as e:
            _logger.error("Save chat history error: %s", str(e))

    def get_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[History]:
        # For production use, this method would need a more complex implementation
        # to read ALL rotated files for the current date. For now, it only reads
        # the primary non-rotated file as per the original structure.
        file_path = self._get_base_file_path()

        if not os.path.exists(file_path):
            return []

        messages = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        messages.append(History.model_validate_json(line))

        except Exception as e:
            _logger.error("Read chat history error: %s", str(e))

        return messages
