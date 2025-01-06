from typing import Dict, Any

from modules.whatsapp import WaUser

class WhatsAppPayloadGenerator:
    """
        Generates whatsapp api payload from given engine template

        template: {
            "stage_name": {.. stage_data ..}
        }
        ```
    """

    def __init__(self, template: Dict[str, Any], user: WaUser) -> None:
        self.template = template
        self.user = user

    def text(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "message": self.template.get("message")
        }

        return data

    def button(self) -> Dict[Any, Any]:
        """
        Method to create a button object to be used in the send_message method.

        This is method is designed to only be used internally by the send_button method.

        Args:
               button[dict]: A dictionary containing the button data
        """
        data = {"type": "list", "action": button.get("action")}
        if button.get("header"):
            data["header"] = {"type": "text", "text": button.get("header")}
        if button.get("body"):
            data["body"] = {"text": button.get("body")}
        if button.get("footer"):
            data["footer"] = {"text": button.get("footer")}
        return data
