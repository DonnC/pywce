from datetime import datetime
from typing import Dict, Any

from pywce.src.constants import SessionConstants, TemplateTypeConstants
from pywce.src.exceptions import EngineInternalException
from pywce.src.models import WhatsAppServiceModel
from pywce.src.services.template_message_processor import TemplateMessageProcessor
from pywce.src.utils import pywce_logger

_logger = pywce_logger(__name__)


class WhatsAppService:
    """
        Generates whatsapp api payload from given engine template

        sends whatsapp message
    """
    _processor: TemplateMessageProcessor

    def __init__(self, model: WhatsAppServiceModel, validate_template: bool = True) -> None:
        self.model = model
        self.template = model.template
        self.model_template_type = self.model.template_type

        self._init_processor(validate_template)

    def _init_processor(self, validate_tpl: bool):
        self._processor = TemplateMessageProcessor(
            template=self.template,
            hook_arg=self.model.hook_arg,
            wa_config=self.model.whatsapp.config,
            template_type=self.model_template_type,
            tag_on_reply=self.model.tag_on_reply,
            validate_template=validate_tpl,
        )

    async def send_message(self, handle_session: bool = True, template: bool = True) -> Dict[str, Any]:
        """
        :param handle_session:
        :param template: process as engine template message else, bypass engine logic
        :return:
        """
        payload: Dict[str, Any] = await self._processor.payload(template)

        # update template type in case there was a processed dynamic template
        self.model_template_type = self._processor.template_type

        match self.model_template_type:
            case TemplateTypeConstants.TEXT:
                response = await self.model.whatsapp.send_message(**payload)

            case TemplateTypeConstants.BUTTON:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.CTA:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.CATALOG:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.SINGLE_PRODUCT:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.MULTI_PRODUCT:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.LIST:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.FLOW:
                response = await self.model.whatsapp.send_interactive(**payload)

            case TemplateTypeConstants.MEDIA:
                response = await self.model.whatsapp.send_media(**payload)

            case TemplateTypeConstants.TEMPLATE:
                response = await self.model.whatsapp.send_template(**payload)

            case TemplateTypeConstants.LOCATION:
                response = await self.model.whatsapp.send_location(**payload)

            case TemplateTypeConstants.REQUEST_LOCATION:
                response = await self.model.whatsapp.request_location(**payload)

            case _:
                raise EngineInternalException(
                    message="Unsupported message type for payload generation",
                    data=f"Stage: {self.model.next_stage} | Type: {self.model_template_type}"
                )

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
