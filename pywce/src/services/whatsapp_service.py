import re
from datetime import datetime
from random import randint
from typing import Dict, Any, List, Union

from pywce.modules import client
from pywce.src.constants import SessionConstants, TemplateConstants, TemplateTypeConstants
from pywce.src.exceptions import EngineInternalException
from pywce.src.models import WhatsAppServiceModel
from pywce.src.services import HookService
from pywce.src.utils import EngineUtil
from pywce.src.utils.engine_logger import pywce_logger

_logger = pywce_logger(__name__)


class WhatsAppService:
    """
        Generates whatsapp api payload from given engine template

        template: {
            "stage_name": {.. stage_data ..}
        }
        ```
    """

    def __init__(self, model: WhatsAppServiceModel, validate_template: bool = True) -> None:
        self.model = model
        self.template = model.template

        if validate_template:
            self._validate_template()

    def _message_id(self) -> Union[str, None]:
        """
        Get message id to reply to
        
        :return: None or message id to reply to 
        """
        if self.model.tag_on_reply is True:
            return self.model.hook_arg.user.msg_id

        msg_id = self.template.get(TemplateConstants.REPLY_MESSAGE_ID, False)

        if isinstance(msg_id, str):
            return msg_id

        return None if msg_id is False else self.model.hook_arg.user.msg_id

    def _validate_template(self) -> None:
        if TemplateConstants.TEMPLATE_TYPE not in self.template:
            raise EngineInternalException("Template type not specified")
        if TemplateConstants.MESSAGE not in self.template:
            raise EngineInternalException("Template message not defined")

    def _process_special_vars(self) -> Dict:
        """
        Process and replace special variables in the template ({{ s.var }} and {{ p.var }}).

        Replace `s.` vars with session data

        Replace `p.` vars with session props data
        """
        session = self.model.hook_arg.session_manager
        user_props = session.get_user_props(self.model.user.wa_id)

        def replace_special_vars(value: Any) -> Any:
            if isinstance(value, str):
                value = re.sub(
                    r"{{\s*s\.([\w_]+)\s*}}",
                    lambda match: session.get(session_id=self.model.user.wa_id, key=match.group(1)) or match.group(0),
                    value
                )

                value = re.sub(
                    r"{{\s*p\.([\w_]+)\s*}}",
                    lambda match: user_props.get(match.group(1), match.group(0)),
                    value
                )

            elif isinstance(value, dict):
                return {key: replace_special_vars(val) for key, val in value.items()}

            elif isinstance(value, list):
                return [replace_special_vars(item) for item in value]

            return value

        return replace_special_vars(self.template)

    def _process_template_hook(self, skip: bool = False) -> None:
        """
        If template has the `template` hook specified, process it
        and resign to self.template
        :return: None
        """
        self.template = self._process_special_vars()

        if skip: return

        if TemplateConstants.TEMPLATE in self.template:
            response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                                hook_arg=self.model.hook_arg)

            self.template = EngineUtil.process_template(
                template=self.template,
                context=response.template_body.render_template_payload
            )

    def _text(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.model.user.wa_id,
            "message": self.template.get(TemplateConstants.MESSAGE),
            "message_id": self._message_id()
        }

        return data

    def _button(self) -> Dict[str, Any]:
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
                    "id": str(button).lower(),
                    "title": button
                }
            })

        data["action"] = {"buttons": buttons_data}

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _cta(self) -> Dict[str, Any]:
        """
        Method to create a Call-To-Action button object to be used in the send_message method.

        Args:
               button[dict]: A dictionary containing the cta button data
        """
        data = {"type": "cta_url"}
        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        data["action"] = {
            "name": "cta_url",
            "parameters": {
                "display_text": message.get("button"),
                "url": message.get(TemplateConstants.MESSAGE_URL)
            }
        }

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _single_product_item(self) -> Dict[str, Any]:
        """
        Method to create a single product message

        Args:
               button[dict]: A dictionary containing the product data
        """
        data = {"type": "product"}

        assert self.template.get(TemplateConstants.MESSAGE) is not None, "template message is missing"

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        assert message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID) is not None, "product id is missing"
        assert message.get(TemplateConstants.MESSAGE_CATALOG_ID) is not None, "catalog id is missing"

        data["action"] = {
            "product_retailer_id": message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID),
            "catalog_id": message.get(TemplateConstants.MESSAGE_CATALOG_ID)
        }

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _multi_product_item(self) -> Dict[str, Any]:
        """
        Method to create a multi product message

        Args:
               button[dict]: A dictionary containing the product data
        """
        data = {"type": "product_list"}

        assert self.template.get(TemplateConstants.MESSAGE) is not None, "template message is missing"

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)
        sections: Dict[str, Dict[str, Dict]] = message.get(TemplateConstants.MESSAGE_SECTIONS)

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        assert message.get(TemplateConstants.MESSAGE_CATALOG_ID) is not None, "catalog id is missing"

        action_data = {"catalog_id": message.get(TemplateConstants.MESSAGE_CATALOG_ID)}

        section_data = []

        for section_title, item_list in sections.items():
            sec_title_data = {"title": section_title}
            sec_title_items = []

            for item in item_list:
                sec_title_items.append({"product_retailer_id": item})

            sec_title_data["product_items"] = sec_title_items

            section_data.append(sec_title_data)

        action_data["sections"] = section_data
        data["action"] = action_data

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _catalog(self) -> Dict[str, Any]:
        """
        Method to create a View Catalog message

        Args:
               button[dict]: A dictionary containing the catalog data
        """
        data = {"type": "catalog_message"}
        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        if message.get(TemplateConstants.MESSAGE_TITLE):
            data["header"] = {"type": "text", "text": message.get(TemplateConstants.MESSAGE_TITLE)}
        if message.get(TemplateConstants.MESSAGE_BODY):
            data["body"] = {"text": message.get(TemplateConstants.MESSAGE_BODY)}
        if message.get(TemplateConstants.MESSAGE_FOOTER):
            data["footer"] = {"text": message.get(TemplateConstants.MESSAGE_FOOTER)}

        action_data = {"name": "catalog_message"}

        if message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID):
            action_data["parameters"] = {
                "thumbnail_product_retailer_id": message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID)
            }

        data["action"] = action_data

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _list(self) -> Dict[str, Any]:
        data = {"type": "list"}

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)
        sections: Dict[str, Dict[str, Dict]] = message.get(TemplateConstants.MESSAGE_SECTIONS)

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

            sec_title_data["rows"] = sec_title_rows

            section_data.append(sec_title_data)

        data["action"] = {
            "button": message.get("button", "Options"),
            "sections": section_data
        }

        return {
            "recipient_id": self.model.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _flow(self) -> Dict[str, Any]:
        """
        Flow template may require initial flow data to be passed, it is handled here
        """
        config = self.model.whatsapp.config
        data = {"type": "flow"}

        flow_initial_payload: Dict or None = None

        if TemplateConstants.TEMPLATE in self.template:
            self.template = self._process_special_vars()

            response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                                hook_arg=self.model.hook_arg)

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
            "message_id": self._message_id(),
            "payload": data
        }

    def _media(self) -> Dict[str, Any]:
        """
        caters for all media types
        """

        MEDIA_MAPPING = {
            "image": client.MessageTypeEnum.IMAGE,
            "video": client.MessageTypeEnum.VIDEO,
            "audio": client.MessageTypeEnum.AUDIO,
            "document": client.MessageTypeEnum.DOCUMENT,
            "sticker": client.MessageTypeEnum.STICKER
        }

        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        data = {
            "recipient_id": self.model.user.wa_id,
            "media": message.get(TemplateConstants.MESSAGE_MEDIA_ID, message.get(TemplateConstants.MESSAGE_URL)),
            "media_type": MEDIA_MAPPING.get(message.get(TemplateConstants.TEMPLATE_TYPE)),
            "caption": message.get(TemplateConstants.MESSAGE_MEDIA_CAPTION),
            "filename": message.get(TemplateConstants.MESSAGE_MEDIA_FILENAME),
            "message_id": self._message_id(),
            "link": message.get(TemplateConstants.MESSAGE_URL) is not None
        }

        return data

    def _location(self) -> Dict[str, Any]:
        message: Dict[str, Any] = self.template.get(TemplateConstants.MESSAGE)

        data = {
            "recipient_id": self.model.user.wa_id,
            "lat": message.get("lat"),
            "lon": message.get("lon"),
            "name": message.get("name"),
            "address": message.get("address"),
            "message_id": self._message_id()
        }

        return data

    def _location_request(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.model.user.wa_id,
            "message": self.template.get(TemplateConstants.MESSAGE),
            "message_id": self._message_id()
        }

        return data

    def _dynamic(self):
        """
        Call template hook and expect template message in hook.template_body.render_template_payload

        Given the dynamic body type in hook.template_body.typ

        The dynamic method must process the payload and sent it
        """
        assert self.template.get(TemplateConstants.TEMPLATE), "template hook is missing"

        response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                            hook_arg=self.model.hook_arg)

        _logger.debug("Dynamic template response: %s", response)

        # TODO: implement dynamic

        match response.template_body.typ:
            case client.MessageTypeEnum.TEXT:
                pass

    async def send_message(self, handle_session: bool = True, template: bool = True) -> Dict[str, Any]:
        """
        :param handle_session:
        :param template: process as engine template message else, bypass engine logic
        :return:
        """
        if template is True:
            self._process_template_hook(
                skip=self.model.template_type == TemplateTypeConstants.FLOW or \
                     self.model.template_type == TemplateTypeConstants.DYNAMIC
            )

        match self.model.template_type:
            case TemplateTypeConstants.TEXT:
                response = await self.model.whatsapp.send_message(**self._text())

            case TemplateTypeConstants.BUTTON:
                response = await self.model.whatsapp.send_interactive(**self._button())

            case TemplateTypeConstants.CTA:
                response = await self.model.whatsapp.send_interactive(**self._cta())

            case TemplateTypeConstants.CATALOG:
                response = await self.model.whatsapp.send_interactive(**self._catalog())

            case TemplateTypeConstants.SINGLE_PRODUCT:
                response = await self.model.whatsapp.send_interactive(**self._single_product_item())

            case TemplateTypeConstants.MULTI_PRODUCT:
                response = await self.model.whatsapp.send_interactive(**self._multi_product_item())

            case TemplateTypeConstants.LIST:
                response = await self.model.whatsapp.send_interactive(**self._list())

            case TemplateTypeConstants.FLOW:
                response = await self.model.whatsapp.send_interactive(**self._flow())

            case TemplateTypeConstants.MEDIA:
                response = await self.model.whatsapp.send_media(**self._media())

            case TemplateTypeConstants.LOCATION:
                response = await self.model.whatsapp.send_location(**self._location())

            case TemplateTypeConstants.REQUEST_LOCATION:
                response = await self.model.whatsapp.request_location(**self._location_request())

            case _:
                raise EngineInternalException(message="Failed to generate whatsapp payload",
                                              data=self.model.next_stage)

        if template is True or \
                self.model.whatsapp.util.was_request_successful(recipient_id=self.model.user.wa_id,
                                                                response_data=response):
            if handle_session is True:
                session = self.model.hook_arg.session_manager
                session_id = self.model.user.wa_id
                current_stage = session.get(session_id=session_id, key=SessionConstants.CURRENT_STAGE)

                session.save(session_id=session_id, key=SessionConstants.PREV_STAGE, data=current_stage)
                session.save(session_id=session_id, key=SessionConstants.CURRENT_STAGE, data=self.model.next_stage)

                _logger.debug(f"Current route set to: {self.model.next_stage}")

                if self.model.handle_session_activity is True:
                    session.save(session_id=session_id, key=SessionConstants.LAST_ACTIVITY_AT,
                                 data=datetime.now().isoformat())

        return response
