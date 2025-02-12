import re
from random import randint
from typing import Dict, Any, List, Union, Optional

from pywce import EngineConstants
from pywce.modules import client
from pywce.modules.whatsapp import WhatsAppConfig
from pywce.src.constants import TemplateConstants, TemplateTypeConstants
from pywce.src.exceptions import EngineInternalException
from pywce.src.models import HookArg
from pywce.src.services import HookService
from pywce.src.utils import EngineUtil, pywce_logger

_logger = pywce_logger(__name__)


class TemplateMessageProcessor:
    """
    Template Message Processor

    Processes template messages, creates whatsapp message bodies from passed templates.
    """
    _message: Union[str, Dict[str, Any]] = None

    def __init__(self,
                 template: Dict[str, Any],
                 hook_arg: HookArg,
                 wa_config: WhatsAppConfig,
                 template_type: TemplateTypeConstants,
                 tag_on_reply: bool = False,
                 validate_template: bool = True
                 ) -> None:
        self.tag_on_reply = tag_on_reply
        self.template_type = template_type
        self.wa_config = wa_config
        self.hook = hook_arg
        self.template = template

        self._setup(validate_template)

    def _setup(self, validate_tpl: bool):
        self.user = self.hook.user

        if validate_tpl:
            self._validate_template()

        self._message = self.template.get(TemplateConstants.MESSAGE)

    def _message_id(self) -> Union[str, None]:
        """
        Get message id to reply to

        :return: None or message id to reply to
        """
        if self.tag_on_reply is True:
            return self.user.msg_id

        msg_id = self.template.get(TemplateConstants.REPLY_MESSAGE_ID, False)

        if isinstance(msg_id, str):
            return msg_id

        return None if msg_id is False else self.user.msg_id

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
        session = self.hook.session_manager
        user_props = session.get_user_props(self.user.wa_id)

        def replace_special_vars(value: Any) -> Any:
            if isinstance(value, str):
                value = re.sub(
                    r"{{\s*s\.([\w_]+)\s*}}",
                    lambda match: session.get(session_id=self.user.wa_id, key=match.group(1)) or match.group(0),
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
        self._setup(True)

        if skip: return

        if TemplateConstants.TEMPLATE in self.template:
            response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                                hook_arg=self.hook)

            self.template = EngineUtil.render_template(
                template=self.template,
                context=response.template_body.render_template_payload
            )

            self._setup(True)

    def _get_common_interactive_fields(self) -> Dict[str, Any]:
        """
        Helper function to get common fields (header, body, footer) if they exist.

        TODO: implement different supported header types for button messages
        """
        interactive_fields = {}

        if self._message.get(TemplateConstants.MESSAGE_TITLE):
            interactive_fields["header"] = {"type": "text", "text": self._message.get(TemplateConstants.MESSAGE_TITLE)}
        if self._message.get(TemplateConstants.MESSAGE_BODY):
            interactive_fields["body"] = {"text": self._message.get(TemplateConstants.MESSAGE_BODY)}
        if self._message.get(TemplateConstants.MESSAGE_FOOTER):
            interactive_fields["footer"] = {"text": self._message.get(TemplateConstants.MESSAGE_FOOTER)}

        return interactive_fields

    def _text(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "message": self._message,
            "message_id": self._message_id()
        }

        return data

    def _button(self) -> Dict[str, Any]:
        """
        Method to create a button object to be used in the send_message method.

        This is method is designed to only be used internally by the send_button method.

        Args:
               button[dict]: A dictionary containing the button data
        """
        buttons: List = self._message.get(TemplateConstants.MESSAGE_BUTTONS)
        data = {
            "type": "button",
            **self._get_common_interactive_fields()
        }

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
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _cta(self) -> Dict[str, Any]:
        """
        Method to create a Call-To-Action button object to be used in the send_message method.

        Args:
               button[dict]: A dictionary containing the cta button data
        """
        data = {"type": "cta_url",
                **self._get_common_interactive_fields(),
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": self._message.get(TemplateConstants.MESSAGE_BUTTON),
                        "url": self._message.get(TemplateConstants.MESSAGE_URL)
                    }
                }}

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _single_product_item(self) -> Dict[str, Any]:
        """
        Method to create a single product message

        Args:
               button[dict]: A dictionary containing the product data
        """
        data = {
            "type": "product",
            **self._get_common_interactive_fields(),
            "action": {
                "product_retailer_id": self._message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID),
                "catalog_id": self._message.get(TemplateConstants.MESSAGE_CATALOG_ID)
            }}

        assert self._message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID) is not None, "product id is missing"
        assert self._message.get(TemplateConstants.MESSAGE_CATALOG_ID) is not None, "catalog id is missing"

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _multi_product_item(self) -> Dict[str, Any]:
        """
        Method to create a multi product message

        Args:
               button[dict]: A dictionary containing the product data
        """
        data = {"type": "product_list", **self._get_common_interactive_fields()}

        sections: Dict[str, Dict[str, Dict]] = self._message.get(TemplateConstants.MESSAGE_SECTIONS)

        assert self._message.get(TemplateConstants.MESSAGE_CATALOG_ID) is not None, "catalog id is missing"

        action_data = {"catalog_id": self._message.get(TemplateConstants.MESSAGE_CATALOG_ID)}

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
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _catalog(self) -> Dict[str, Any]:
        """
        Method to create a View Catalog message

        Args:
               button[dict]: A dictionary containing the catalog data
        """
        data = {"type": "catalog_message", **self._get_common_interactive_fields()}

        action_data = {"name": "catalog_message"}

        if self._message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID):
            action_data["parameters"] = {
                "thumbnail_product_retailer_id": self._message.get(TemplateConstants.MESSAGE_CATALOG_PRODUCT_ID)
            }

        data["action"] = action_data

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _list(self) -> Dict[str, Any]:
        data = {"type": "list", **self._get_common_interactive_fields()}

        sections: Dict[str, Dict[str, Dict]] = self._message.get(TemplateConstants.MESSAGE_SECTIONS)

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
            "button": self._message.get(TemplateConstants.MESSAGE_BUTTON, "Options"),
            "sections": section_data
        }

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _flow(self) -> Dict[str, Any]:
        """
        Flow template may require initial flow data to be passed, it is handled here
        """
        data = {"type": "flow", **self._get_common_interactive_fields()}

        flow_initial_payload: Optional[Dict] = None

        if TemplateConstants.TEMPLATE in self.template:
            response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                                hook_arg=self.hook)

            flow_initial_payload = response.template_body.initial_flow_payload

            self.template = EngineUtil.render_template(
                template=self.template,
                context=response.template_body.render_template_payload
            )
            self._setup(True)

        action_payload = {"screen": self._message.get(TemplateConstants.MESSAGE_NAME)}

        if flow_initial_payload is not None:
            action_payload["data"] = flow_initial_payload

        data["action"] = {
            "name": "flow",
            "parameters": {
                "flow_message_version": self.wa_config.flow_version,
                "flow_action": self.wa_config.flow_action,
                "mode": "published" if self._message.get(TemplateConstants.MESSAGE_FLOW_DRAFT) is None else "draft",
                "flow_token": f"{self._message.get(TemplateConstants.MESSAGE_NAME)}_{self.user.wa_id}_{randint(99, 9999)}",
                "flow_id": self._message.get(TemplateConstants.MESSAGE_ID),
                "flow_cta": self._message.get(TemplateConstants.MESSAGE_BUTTON),
                "flow_action_payload": action_payload
            }
        }

        return {
            "recipient_id": self.user.wa_id,
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

        data = {
            "recipient_id": self.user.wa_id,
            "media": self._message.get(TemplateConstants.MESSAGE_ID,
                                       self._message.get(TemplateConstants.MESSAGE_URL)),
            "media_type": MEDIA_MAPPING.get(self._message.get(TemplateConstants.TEMPLATE_TYPE)),
            "caption": self._message.get(TemplateConstants.MESSAGE_MEDIA_CAPTION),
            "filename": self._message.get(TemplateConstants.MESSAGE_MEDIA_FILENAME),
            "message_id": self._message_id(),
            "link": self._message.get(TemplateConstants.MESSAGE_URL) is not None
        }

        return data

    def _location(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "lat": self._message.get(TemplateConstants.MESSAGE_LOC_LAT),
            "lon": self._message.get(TemplateConstants.MESSAGE_LOC_LON),
            "name": self._message.get(TemplateConstants.MESSAGE_NAME),
            "address": self._message.get(TemplateConstants.MESSAGE_LOC_ADDRESS),
            "message_id": self._message_id()
        }

        return data

    def _location_request(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "message": self._message,
            "message_id": self._message_id()
        }

        return data

    def _dynamic(self):
        """
        Call template hook and expect template message in hook.template_body.render_template_payload

        Given the dynamic body type in hook.template_body.typ

        The dynamic method must process the payload and sent it

        The dynamic payload must be same as template json message body
        """
        assert self.template.get(TemplateConstants.TEMPLATE), "template hook is missing"

        response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                            hook_arg=self.hook)

        _logger.debug("Dynamic template response: %s", response)

        self.template_type = response.template_body.typ
        self._message = response.template_body.render_template_payload

    def _whatsapp_template(self):
        """
        Call template hook and expect whatsapp template body in hook.template_body.render_template_payload

        The response dict must contain **EngineConstants.WHATSAPP_TEMPLATE_KEY** key with a **List**
        of template components

        The dynamic method must process the payload and sent it

        The dynamic payload must be same as template json message body
        """
        assert self.template.get(TemplateConstants.TEMPLATE), "template hook is missing"
        assert self._message.get(TemplateConstants.MESSAGE_NAME) is not None, "template name is missing"

        response = HookService.process_hook(hook_dotted_path=self.template.get(TemplateConstants.TEMPLATE),
                                            hook_arg=self.hook)

        _logger.debug("WhatsApp Template, template response: %s", response)

        components: List = response.template_body.render_template_payload.get(EngineConstants.WHATSAPP_TEMPLATE_KEY, [])

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "template": self._message.get(TemplateConstants.MESSAGE_NAME),
            "lang": self._message.get(TemplateConstants.MESSAGE_TEMPLATE_LANG, "en_US"),
            "components": components
        }

    def _generate_payload(self, template: bool = True) -> Dict[str, Any]:
        """
        :param template: process as engine template message else, bypass engine logic
        :return:
        """
        if template is True:
            self._process_template_hook(
                skip=self.template_type == TemplateTypeConstants.FLOW or \
                     self.template_type == TemplateTypeConstants.DYNAMIC or \
                     self.template_type == TemplateTypeConstants.TEMPLATE
            )

        match self.template_type:
            case TemplateTypeConstants.TEXT:
                return self._text()

            case TemplateTypeConstants.TEMPLATE:
                return self._whatsapp_template()

            case TemplateTypeConstants.BUTTON:
                return self._button()

            case TemplateTypeConstants.CTA:
                return self._cta()

            case TemplateTypeConstants.CATALOG:
                return self._catalog()

            case TemplateTypeConstants.SINGLE_PRODUCT:
                return self._single_product_item()

            case TemplateTypeConstants.MULTI_PRODUCT:
                return self._multi_product_item()

            case TemplateTypeConstants.LIST:
                return self._list()

            case TemplateTypeConstants.FLOW:
                return self._flow()

            case TemplateTypeConstants.MEDIA:
                return self._media()

            case TemplateTypeConstants.LOCATION:
                return self._location()

            case TemplateTypeConstants.REQUEST_LOCATION:
                return self._location_request()

            case _:
                raise EngineInternalException(
                    message=f"Type not supported for payload generation: {self.template_type}")

    def payload(self, template: bool = True) -> Dict[str, Any]:
        """
            :param template: process as engine template message else, bypass engine logic
            :return:
        """
        if self.template_type == TemplateTypeConstants.DYNAMIC:
            self._dynamic()

        return self._generate_payload(template=template)
