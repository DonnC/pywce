from dataclasses import dataclass
from typing import Any

from modules.whatsapp import MessageTypeEnum


@dataclass
class ResponseStructure:
    body: Any = None
    model: MessageTypeEnum = MessageTypeEnum.UNKNOWN
