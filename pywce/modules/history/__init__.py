import datetime
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Any

from pydantic import BaseModel

_logger = logging.getLogger(__name__)


class History(BaseModel):
    role: str
    message_type: str
    timestamp: str  # ISO format string
    content: Optional[str] = None
    stage: Optional[str] = None
    metadata: Optional[Any] = None


class IHistoryManager(ABC):
    """
        A history interface to log every message interaction between user and bot
    """

    @abstractmethod
    def log_message(self, session_id: str, message: History):
        """Append a message to the history log."""
        pass

    @abstractmethod
    def get_history(self, session_id: str, limit: int = 50) -> List[History]:
        """Retrieve recent history (optional implementation)."""
        pass


class FileHistoryManager(IHistoryManager):
    def __init__(self, base_dir: str = "pywce_history"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            _logger.debug("Saving chat history to dir: %s", self.base_dir)

    def _get_file_path(self, session_id: str) -> str:
        # File naming: {wa_id}_{YYYY-MM-DD}.jsonl
        # e.g., 26377123456_2025-11-30.jsonl
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"{session_id}_{today}.jsonl"
        return os.path.join(self.base_dir, filename)

    def log_message(self, session_id: str, message: History):
        file_path = self._get_file_path(session_id)

        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(message.model_dump_json() + "\n")
        except Exception as e:
            _logger.error("Save chat history error: %s", str(e))

    def get_history(self, session_id: str, limit: int = 50) -> List[History]:
        # For simplicity, we just read TODAY'S file.
        # A robust implementation would check yesterday's file if today's is empty.
        file_path = self._get_file_path(session_id)

        if not os.path.exists(file_path):
            return []

        messages = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        messages.append(History.model_validate_json(json.loads(line)))

        except Exception as e:
            _logger.error("Read chat history error: %s", str(e))
            return []

        return messages
