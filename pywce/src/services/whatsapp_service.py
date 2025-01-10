import re
from datetime import datetime
from random import randint
from typing import Dict, Any, List

from pywce.engine_logger import get_engine_logger
from pywce.modules.whatsapp import MessageTypeEnum
from pywce.src.constants.session import SessionConstants
from pywce.src.constants.template import TemplateConstants
from pywce.src.constants.template_type import TemplateTypeConstants
from pywce.src.exceptions import EngineInternalException
from pywce.src.models import WhatsAppServiceModel
from pywce.src.services.hook_service import HookService
from pywce.src.utils.engine_util import EngineUtil


class WhatsAppService:
    """
        Generates whatsapp api payload from given engine template

        template: {
            "stage_name": {.. stage_data ..}
        }
        ```
    """

    def __init__(self, model: WhatsAppServiceModel, validate_template:bool=True) -> None:
        self.model = model
        self.template = model.template

        self.logger = get_engine_logger(__name__)

        if validate_template:
            self.__validate_template__()

    def __validate_template__(self) -> None:
        if TemplateConstants.TEMPLATE_TYPE not in self.template:
            raise EngineInternalException("Template type not specified")
        if TemplateConstants.MESSAGE not in self.template:
            raise EngineInternalException("Template message not defined")

    def __process_special_vars__(self) -> Dict:
        """
        Process and replace special variables in the template ({{ s.var }} and {{ p.var }}).
        """
        session = self.model.hook_arg.session_manager
        user_props = session.get_user_props(self.model.user.wa_id)

        def replace_special_vars(value):
            if isinstance(value, str):
                # Replace `s.` vars with session data
                value = re.sub(
                    r"{{\s*s\.([\w_]+)\s*}}",
                    lambda match: session.get(session_id=self.model.user.wa_id, key=match.group(1)) or match.group(0),
                    value
                )

                # Replace `p.` vars with props data
                value = re.sub(
                    r"{{\s*p\.([\w_]+)\s*}}",
                    lambda match: user_props.get(match.group(1), match.group(0)),
                    value
                )

            return value

        if isinstance(self.template, dict):
            return {key: self.__process_special_vars__() for key, value in self.template.items()}
        else:
            return replace_special_vars(self.template)

    def __process_template_hook__(self, skip: bool = False) -> None:
        """
        If template has the `template` hook specified, process it
        and resign to self.template
        :return: None
        """
        if skip: return

        if TemplateConstants.TEMPLATE in self.template:
            self.template = self.__process_special_vars__()

            response = HookService.process_hook(
                hook_name=self.template.get(TemplateConstants.TEMPLATE_TYPE),
                hook_arg=self.model.hook_arg
            )

            self.template = EngineUtil.process_template(
                template=self.template,
                context=response.template_body.render_template_payload
            )

    def __text__(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.model.user.wa_id,
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

        TODO: implement different supported button header types
        """
        data = {"type": "button"}
        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)
        buttons: List = message.get("buttons")

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        buttons_data = []
        for button in buttons:
            buttons_data.append({
                "type": "reply",
                "reply": {
                    "id": button,
                    "title": button
                }
            })

        data["action"] = {"buttons": buttons_data}

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID),
            "payload": data
        }

    def __list__(self) -> Dict[str, Any]:
        data = {"type": "list"}

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)
        sections: Dict[str, Dict[str, Dict]] = message.get("sections")

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        section_data = []
        for section_title, inner_sections in sections.items():
            sec_title_data = {"title": section_title}
            sec_title_rows = []

            for _id, _section in inner_sections.items():
                sec_title_rows.append({
                    "id": _id,
                    "title": _section.get("title"),
                    "description": _section.get("description")
                })

            section_data.append(sec_title_data)

        data["action"] = {
            "button": message.get("button", "Options"),
            "sections": section_data
        }

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID),
            "payload": data
        }

    def __flow__(self) -> Dict[str, Any]:
        """
        Flow template may require initial flow data to be passed, it is handled here
        """
        config = self.model.whatsapp.config
        data = {"type": "flow"}

        flow_initial_payload: Dict = None

        if TemplateConstants.TEMPLATE in self.template:
            self.template = self.__process_special_vars__()

            response = HookService.process_hook(
                hook_name=self.template.get(TemplateConstants.TEMPLATE_TYPE),
                hook_arg=self.model.hook_arg
            )

            flow_initial_payload = response.template_body.initial_flow_payload

            self.template = EngineUtil.process_template(
                template=self.template,
                context=response.template_body.render_template_payload
            )

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        action_payload = {"screen": message.get('name')}

        if flow_initial_payload:
            action_payload["data"] = flow_initial_payload

        data["action"] = {
            "name": "flow",
            "parameters": {
                "flow_message_version": config.flow_version,
                "flow_action": config.flow_action,
                "mode": "published" if message.get("draft") is None else "draft",
                "flow_token": f"{message.get('name')}_{self.model.user.wa_id}_{randint(99, 9999)}",
                "flow_id": message.get("id"),
                "flow_cta": message.get("button"),
                "flow_action_payload": action_payload
            }
        }

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID),
            "payload": data
        }

    def __media__(self) -> Dict[str, Any]:
        """
        caters for all media types
        """

        MEDIA_MAPPING = {
            "image": MessageTypeEnum.IMAGE,
            "video": MessageTypeEnum.VIDEO,
            "audio": MessageTypeEnum.AUDIO,
            "document": MessageTypeEnum.DOCUMENT,
            "sticker": MessageTypeEnum.STICKER
        }

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        data = {
            "recipient_id": self.model.user.wa_id,
            "media": message.get(TemplateConstants.MESSAGE_MEDIA_ID, message.get(TemplateConstants.MESSAGE_MEDIA_URL)),
            "media_type": MEDIA_MAPPING.get(message.get(TemplateConstants.TEMPLATE_TYPE)),
            "caption": message.get(TemplateConstants.MESSAGE_MEDIA_CAPTION),
            "filename": message.get(TemplateConstants.MESSAGE_MEDIA_FILENAME),
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID),
            "link": message.get(TemplateConstants.MESSAGE_MEDIA_URL) is not None
        }

        return data

    def __location__(self) -> Dict[str, Any]:
        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        data = {
            "recipient_id": self.model.user.wa_id,
            "lat": message.get("lat"),
            "lon": message.get("lon"),
            "name": message.get("name"),
            "address": message.get("address"),
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID)
        }

        return data

    def __location_request__(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.model.user.wa_id,
            "message": self.template.get(TemplateConstants.MESSAGE),
            "message_id": self.template.get(TemplateConstants.REPLY_MESSAGE_ID)
        }

        return data

    async def send_message(self, handle_session: bool = True, template: bool = True) -> Dict[str, Any]:
        """
        :param handle_session:
        :param template: process as engine template message else, bypass engine logic
        :return:
        """
        self.__process_template_hook__(
            skip=self.model.template_type == TemplateTypeConstants.FLOW or \
                 self.model.template_type == TemplateTypeConstants.DYNAMIC
        )

        response: Dict = {}

        match self.model.template_type:
            case TemplateTypeConstants.TEXT:
                response = await self.model.whatsapp.send_message(**self.__text__())

            case TemplateTypeConstants.BUTTON:
                response = await self.model.whatsapp.send_interactive(**self.__button__())

            case TemplateTypeConstants.LIST:
                response = await self.model.whatsapp.send_interactive(**self.__list__())

            case TemplateTypeConstants.FLOW:
                response = await self.model.whatsapp.send_interactive(**self.__flow__())

            case TemplateTypeConstants.MEDIA:
                response = await self.model.whatsapp.send_media(**self.__media__())

            case TemplateTypeConstants.LOCATION:
                response = await self.model.whatsapp.send_location(**self.__location__())

            case TemplateTypeConstants.REQUEST_LOCATION:
                response = await self.model.whatsapp.request_location(**self.__location_request__())

            case _:
                raise EngineInternalException(message="Failed to generate whatsapp payload",
                                              data=self.model.next_stage)

        if self.model.whatsapp.util.is_request_successful(recipient_id=self.model.user.wa_id, response_data=response):
            if handle_session is True:
                session = self.model.hook_arg.session_manager
                session_id = self.model.user.wa_id
                current_stage = session.get(session_id=session_id, key=SessionConstants.CURRENT_STAGE)

                session.save(session_id=session_id, key=SessionConstants.PREV_STAGE, data=current_stage)
                session.save(session_id=session_id, key=SessionConstants.CURRENT_STAGE, data=self.model.next_stage)

                self.logger.info(f"Current route set to: {self.model.next_stage}")

                if self.model.handle_session_activity is True:
                    session.save(session_id=session_id, key=SessionConstants.LAST_ACTIVITY_AT,
                                 data=datetime.now().isoformat())

        return response
