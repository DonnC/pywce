from typing import Optional

from pydantic import BaseModel


class WaUser(BaseModel):
    name: Optional[str] = None
    wa_id: Optional[str] = None
    msg_id: Optional[str] = None
    timestamp: Optional[str] = None

    def wa_validator(self):
        assert self.wa_id is not None, "WhatsApp id should not be None"
        assert self.msg_id is not None, "WhatsApp msg id should not be None"
        assert self.timestamp is not None, "WhatsApp timestamp should not be None"
