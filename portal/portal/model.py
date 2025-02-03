from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Message:
    sender: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __str__(self):
        return f"[{self.timestamp}] {self.sender}: {self.content}"


@dataclass
class Chat:
    sender: str
    messages: List[Message] = field(default_factory=list)

    def __str__(self):
        return f"[{self.sender}] {self.messages}"
