from dataclasses import dataclass
from typing import Any, Dict

from pywce.modules.whatsapp.model.message_type_enum import MessageTypeEnum

@dataclass
class ResponseStructure:
    body: Any = None
    typ: MessageTypeEnum = MessageTypeEnum.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {"body": self.body, "type": self.typ}
