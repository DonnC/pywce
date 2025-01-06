from typing import Dict, Any

from modules.whatsapp import WaUser
from src.constants.template import TemplateConstants


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
            "message": self.template.get(TemplateConstants.MESSAGE),
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID)
        }

        return data

    def button(self) -> Dict[str, Any]:
        """
        Method to create a button object to be used in the send_message method.

        This is method is designed to only be used internally by the send_button method.

        Args:
               button[dict]: A dictionary containing the button data
        """
        data = {"type": "list", "action": "reply"}
        # TODO: verify button action

        if self.template.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": self.template.get(TemplateConstants.MESSAGE_TITLE)}
        if self.template.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": self.template.get(TemplateConstants.MESSAGE_BODY)}
        if self.template.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": self.template.get(TemplateConstants.MESSAGE_FOOTER)}

        return data

    # TODO: implement other template types supporting supported message types
