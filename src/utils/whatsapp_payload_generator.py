from typing import Dict, Any

from modules.whatsapp import WaUser, ResponseStructure, MessageTypeEnum
from src.constants.template import TemplateConstants
from src.exceptions import EngineInternalException
from src.models import HookArg


class WhatsAppPayloadGenerator:
    """
        Generates whatsapp api payload from given engine template

        template: {
            "stage_name": {.. stage_data ..}
        }
        ```
    """

    def __init__(self, template: Dict, response_structure: ResponseStructure, stage: str, hook_arg: HookArg,
                 user: WaUser) -> None:
        self.payload = response_structure
        self.template = template
        self.stage = stage
        self.user = user

        self.__validate_template__()

    def __validate_template__(self) -> None:
        if TemplateConstants.TEMPLATE_TYPE not in self.template:
            raise EngineInternalException("Template type not specified")
        if TemplateConstants.MESSAGE not in self.template:
            raise EngineInternalException("Template message not defined")

    def __process_template_hook__(self) -> None:
        """
        If template has the `template` hook specified, process it
        and resign to self.template
        :return: None
        """
        if TemplateConstants.TEMPLATE in self.template:
            pass
        pass

    def __text__(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "message": self.template.get(TemplateConstants.MESSAGE),
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID)
        }

        return data

    def __button__(self) -> Dict[str, Any]:
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

    def generate_payload(self) -> Dict[str, Any]:
        match self.payload.model:
            case MessageTypeEnum.TEXT:
                return self.__text__()

            case MessageTypeEnum.BUTTON:
                pass

            case MessageTypeEnum.LOCATION:
                pass

            case MessageTypeEnum.INTERACTIVE:
                pass

            case MessageTypeEnum.IMAGE | MessageTypeEnum.STICKER | MessageTypeEnum.DOCUMENT | MessageTypeEnum.AUDIO | MessageTypeEnum.VIDEO:
                pass

            case MessageTypeEnum.INTERACTIVE_BUTTON | MessageTypeEnum.INTERACTIVE_FLOW | MessageTypeEnum.INTERACTIVE_LIST:
                pass

            case _:
                raise EngineInternalException(message="Failed to generate whatsapp payload",
                                              data=self.stage)

        raise EngineInternalException(message="Failed to generate whatsapp payload",
                                      data=self.stage)
