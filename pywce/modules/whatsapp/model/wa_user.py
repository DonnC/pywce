from dataclasses import dataclass

@dataclass
class WaUser:
    name: str = None
    wa_id: str = None
    msg_id: str = None
    timestamp: str = None

    def validate(self):
        assert self.wa_id
        assert self.msg_id
        assert self.timestamp