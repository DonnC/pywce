from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pywce.modules.whatsapp.model.message_type_enum import MessageTypeEnum
from pywce.modules.whatsapp.model.response_structure import ResponseStructure
from pywce.modules.whatsapp.model.wa_user import WaUser


@dataclass
class SentRecord:
    method: str
    payload: dict[str, Any]


class FakeWhatsAppUtil:
    def webhook_challenge(self, mode, challenge, token):
        return mode == "subscribe" and challenge is not None and token is not None

    def is_valid_webhook_message(self, webhook_data):
        return webhook_data.get("valid", True)

    def get_wa_user(self, webhook_data):
        return webhook_data["user"]

    def get_response_structure(self, webhook_data):
        return webhook_data["response"]

    def get_user_input(self, response_model):
        return response_model.body, None

    def get_response_message_id(self, response_data):
        return response_data.get("message_id")

    def was_request_successful(self, recipient_id, response_data):
        return True


class FakeWhatsApp:
    def __init__(self):
        self.util = FakeWhatsAppUtil()
        self.sent: list[SentRecord] = []
        self.config = SimpleNamespace(flow_version="3", flow_action="navigate")

    def _record(self, method: str, **payload):
        self.sent.append(SentRecord(method=method, payload=payload))
        return {"message_id": f"{method}-{len(self.sent)}"}

    def send_message(self, **payload):
        return self._record("send_message", **payload)

    def send_interactive(self, **payload):
        return self._record("send_interactive", **payload)

    def send_template(self, **payload):
        return self._record("send_template", **payload)

    def send_media(self, **payload):
        return self._record("send_media", **payload)

    def send_location(self, **payload):
        return self._record("send_location", **payload)

    def request_location(self, **payload):
        return self._record("request_location", **payload)

    def send_reaction(self, **payload):
        return self._record("send_reaction", **payload)

    def mark_as_read(self, message_id: str):
        return self._record("mark_as_read", message_id=message_id)

    def show_typing_indicator(self, message_id: str):
        return self._record("show_typing_indicator", message_id=message_id)


def fixtures_dir(*parts: str) -> Path:
    return Path(__file__).parent / "fixtures" / Path(*parts)


def make_webhook_payload(
    body: Any,
    msg_type: MessageTypeEnum = MessageTypeEnum.TEXT,
    *,
    wa_id: str = "263771234567",
    name: str = "Test User",
    msg_id: str = "wamid-1",
    timestamp: str | None = None,
    valid: bool = True,
):
    ts = timestamp or str(datetime.now().timestamp())
    return {
        "valid": valid,
        "user": WaUser(name=name, wa_id=wa_id, msg_id=msg_id, timestamp=ts),
        "response": ResponseStructure(body=body, typ=msg_type),
    }

