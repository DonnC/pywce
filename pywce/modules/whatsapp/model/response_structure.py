from dataclasses import dataclass
from typing import Any

from .message_type_enum import  MessageTypeEnum

@dataclass
class ResponseStructure:
    body: Any = None
    typ: MessageTypeEnum = MessageTypeEnum.UNKNOWN
