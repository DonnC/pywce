import re
from random import randint
from typing import Dict, Any, List, Union, Optional

import pywce.src.templates as templates
from pywce.modules import client
from pywce.src.constants import EngineConstants
from pywce.src.exceptions import EngineInternalException
from pywce.src.models import WhatsAppServiceModel
from pywce.src.utils.engine_util import EngineUtil
from pywce.src.utils.hook_util import HookUtil


class TemplateMessageProcessor:
    """
    Template Message Processor

    Processes templates messages, creates whatsapp message body from passed templates.
    """
    template: templates.EngineTemplate

    def __init__(self,
                 template: templates.EngineTemplate,
                 whatsapp_model: WhatsAppServiceModel
                 ) -> None:
        self.config = whatsapp_model.config
        self.hook = whatsapp_model.hook_arg
        self.template = template

        self._setup()

    def _setup(self):
        self.user = self.hook.user

    def _message_id(self) -> Union[str, None]:
        """
        Get message id to reply to

        :return: None or message id to reply to
        """
        return self.user.msg_id if self.config.tag_on_reply else self.template.reply_message_id

    def _process_special_vars(self) -> templates.EngineTemplate:
        """
        Process and replace special variables in the templates ({{ s.var }} and {{ p.var }}).

        eg {{ s.var_name_in_session }} or {{ p.prop_name }}

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

        dict_template = replace_special_vars(templates.Template.as_dict(self.template))

        return templates.Template.as_model(dict_template)

    def _process_template_hook(self, skip: bool = False) -> None:
        """
        If templates has the `templates` hook specified, process it
        and reassign to self.templates
        :return: None
        """
        self.template = self._process_special_vars()
        self._setup()

        if skip: return

        if self.config.external_renderer is not None:
            rendered_dict = self.config.external_renderer(
                template_dict=templates.Template.as_dict(self.template),
                hook_path=self.template.template,
                hook_arg=self.hook
            )
            self.template = templates.Template.as_model(rendered_dict)

        else:
            if self.template.template is not None:
                response = HookUtil.process_hook(hook=self.template.template,
                                                 arg=self.hook
                                                 )

                self.template = templates.Template.as_model(EngineUtil.render_template(
                    template=templates.Template.as_dict(self.template),
                    context=response.template_body.render_template_payload
                ))

        self._setup()

    def _get_common_interactive_fields(self) -> Dict[str, Any]:
        """
        Helper function to get common fields (header, body, footer) if they exist.

        TODO: implement different supported header types for quick reply button messages
        """
        _message: templates.BaseInteractiveMessage = self.template.message
        interactive_fields = {"body": {"text": _message.body}}

        if _message.title is not None:
            interactive_fields["header"] = {"type": "text", "text": _message.title}

        if _message.footer is not None:
            interactive_fields["footer"] = {"text": _message.footer}

        return interactive_fields

    def _text(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "message": self.template.message,
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
        buttons: List = self.template.message.buttons
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
                        "display_text": self.template.message.button,
                        "url": self.template.message.url
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
                "product_retailer_id": self.template.message.product_id,
                "catalog_id": self.template.message.catalog_id
            }}

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

        action_data = {"catalog_id": self.template.message.catalog_id}

        section_data = []

        for section in self.template.message.sections:
            sec_title_data = {"title": section.title}
            sec_title_items = []

            for item in section.products:
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

        if self.template.message.product_id is not None:
            action_data["parameters"] = {
                "thumbnail_product_retailer_id": self.template.message.product_id
            }

        data["action"] = action_data

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _list(self) -> Dict[str, Any]:
        data = {"type": "list", **self._get_common_interactive_fields()}

        section_data = []

        for section in self.template.message.sections:
            sec_title_data = {"title": section.title}
            sec_title_rows = []

            for row in section.rows:
                sec_title_rows.append({
                    "id": row.identifier,
                    "title": row.title,
                    "description": row.description
                })

            sec_title_data["rows"] = sec_title_rows

            section_data.append(sec_title_data)

        data["action"] = {
            "button": self.template.message.button,
            "sections": section_data
        }

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "payload": data
        }

    def _flow(self) -> Dict[str, Any]:
        """
        Flow templates may require initial flow data to be passed, it is handled here
        """
        data = {"type": "flow", **self._get_common_interactive_fields()}

        flow_initial_payload: Optional[Dict] = None

        if self.template.template is not None:
            response = HookUtil.process_hook(hook=self.template.template,
                                             arg=self.hook
                                             )

            flow_initial_payload = response.template_body.flow_payload

            self.template = EngineUtil.render_template(
                template=self.template,
                context=response.template_body.render_template_payload
            )
            self._setup()

        action_payload = {"screen": self.template.message.name}

        if flow_initial_payload is not None:
            action_payload["data"] = flow_initial_payload

        flow_token = f"{self.template.message.name}_{self.user.wa_id}_{randint(99, 9999)}"

        data["action"] = {
            "name": "flow",
            "parameters": {
                "flow_message_version": self.config.whatsapp.config.flow_version,
                "flow_action": self.config.whatsapp.config.flow_action,
                "mode": "draft" if self.template.message.draft else "published",
                "flow_token": self.template.message.token if self.template.message.token else flow_token,
                "flow_id": self.template.message.flow_id,
                "flow_cta": self.template.message.button,
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
            "media": self.template.message.media_id or self.template.message.url,
            "media_type": MEDIA_MAPPING.get(self.template.message.kind),
            "caption": self.template.message.caption,
            "filename": self.template.message.filename,
            "message_id": self._message_id(),
            "link": self.template.message.url is not None
        }

        return data

    def _location(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "lat": self.template.message.lat,
            "lon": self.template.message.lon,
            "name": self.template.message.name,
            "address": self.template.message.address,
            "message_id": self._message_id()
        }

        return data

    def _location_request(self) -> Dict[str, Any]:
        data = {
            "recipient_id": self.user.wa_id,
            "message": self.template.message,
            "message_id": self._message_id()
        }

        return data

    def _dynamic(self):
        """
        Call templates hook and expect templates message in hook.template_body.render_template_payload

        Given the dynamic body type in hook.template_body.typ

        The dynamic method must process the payload and sent it

        The dynamic payload must be same as templates json message body
        """
        assert self.template.template is not None, "templates hook is missing"

        response = HookUtil.process_hook(hook=self.template.template,
                                         arg=self.hook
                                         )

        self.template = response.template_body.dynamic_template

    def _whatsapp_template(self):
        """
        Call templates hook and expect whatsapp templates body in hook.template_body.render_template_payload

        The response dict must contain **EngineConstants.WHATSAPP_TEMPLATE_KEY** key with a **List**
        of templates components

        The dynamic method must process the payload and sent it

        The dynamic payload must be same as whatsapp templates json message body
        """
        assert self.template.template is not None, "templates hook is missing"

        response = HookUtil.process_hook(hook=self.template.template,
                                         arg=self.hook
                                         )

        components: List = response.template_body.render_template_payload.get(EngineConstants.WHATSAPP_TEMPLATE_KEY, [])

        return {
            "recipient_id": self.user.wa_id,
            "message_id": self._message_id(),
            "templates": self.template.message.name,
            "lang": self.template.message.language,
            "components": components
        }

    def _generate_payload(self, template: bool = True) -> Dict[str, Any]:
        """
        :param template: process as engine templates message else, bypass engine logic
        :return:
        """
        
        if template:
            self._process_template_hook(
                skip=isinstance(self.template, templates.FlowTemplate) or \
                     isinstance(self.template, templates.DynamicTemplate) or \
                     isinstance(self.template, templates.TemplateTemplate)
            )

        if isinstance(self.template, templates.TextTemplate):
            return self._text()

        elif isinstance(self.template, templates.TemplateTemplate):
            return self._whatsapp_template()

        elif isinstance(self.template, templates.ButtonTemplate):
            return self._button()

        elif isinstance(self.template, templates.CtaTemplate):
            return self._cta()

        elif isinstance(self.template, templates.CatalogTemplate):
            return self._catalog()

        elif isinstance(self.template, templates.ProductTemplate):
            return self._single_product_item()

        elif isinstance(self.template, templates.ProductsMessage):
            return self._multi_product_item()

        elif isinstance(self.template, templates.ListTemplate):
            return self._list()

        elif isinstance(self.template, templates.FlowTemplate):
            return self._flow()

        elif isinstance(self.template, templates.MediaTemplate):
            return self._media()

        elif isinstance(self.template, templates.LocationTemplate):
            return self._location()

        elif isinstance(self.template, templates.RequestLocationTemplate):
            return self._location_request()

        else:
            raise EngineInternalException(
                message=f"Type not supported for payload generation: {self.template.__class__.__name__}")

    def payload(self, template: bool = True) -> Dict[str, Any]:
        """
            :param template: process as engine templates message else, bypass engine logic
            :return:
        """
        override_template = template

        if isinstance(self.template, templates.DynamicTemplate):
            override_template = False
            self._dynamic()

        return self._generate_payload(template=override_template)
