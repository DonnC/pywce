import logging
from datetime import datetime
from typing import Dict, Any

import pywce.src.templates as templates
from pywce.src.constants import SessionConstants
from pywce.src.exceptions import EngineInternalException
from pywce.src.models import WhatsAppServiceModel
from pywce.src.services.template_message_processor import TemplateMessageProcessor

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
        Generates whatsapp api payload from given engine templates

        sends whatsapp message
    """
    _processor: TemplateMessageProcessor

    def __init__(self, model: WhatsAppServiceModel) -> None:
        self.model = model
        self.template = model.template

        self._processor = TemplateMessageProcessor(
            template=model.template,
            whatsapp_model=model
        )

    def send_message(self, handle_session: bool = True, template: bool = True) -> Dict[str, Any]:
        """
        :param handle_session:
        :param template: process as engine templates message else, bypass engine logic
        :return:
        """
        payload: Dict[str, Any] = self._processor.payload(template)
        _tpl = self._processor.template

        is_interactive: bool = isinstance(_tpl, templates.ButtonTemplate) or \
                               isinstance(_tpl, templates.CtaTemplate) or \
                               isinstance(_tpl, templates.CatalogTemplate) or \
                               isinstance(_tpl, templates.ProductTemplate) or \
                               isinstance(_tpl, templates.MultiProductTemplate) or \
                               isinstance(_tpl, templates.ListTemplate) or \
                               isinstance(_tpl, templates.FlowTemplate)

        if is_interactive:
            response = self.model.config.whatsapp.send_interactive(**payload)

        elif isinstance(_tpl, templates.TextTemplate):
            response = self.model.config.whatsapp.send_message(**payload)

        elif isinstance(_tpl, templates.TemplateTemplate):
            response = self.model.config.whatsapp.send_template(**payload)

        elif isinstance(_tpl, templates.MediaTemplate):
            response = self.model.config.whatsapp.send_media(**payload)

        elif isinstance(_tpl, templates.LocationTemplate):
            response = self.model.config.whatsapp.send_location(**payload)

        elif isinstance(_tpl, templates.RequestLocationTemplate):
            response = self.model.config.whatsapp.request_location(**payload)

        else:
            raise EngineInternalException(
                message="Unsupported message type for payload generation",
                data=f"Stage: {self.model.next_stage} | Type: {_tpl.__class__.__name__}"
            )

        if template or \
                self.model.config.whatsapp.util.was_request_successful(recipient_id=self.model.hook_arg.user.wa_id,
                                                                       response_data=response):

            if handle_session:
                session = self.model.hook_arg.session_manager
                session_id = self.model.hook_arg.user.wa_id
                current_stage = session.get(session_id=session_id, key=SessionConstants.CURRENT_STAGE)

                session.save(session_id=session_id, key=SessionConstants.PREV_STAGE, data=current_stage)
                session.save(session_id=session_id, key=SessionConstants.CURRENT_STAGE, data=self.model.next_stage)

                logger.debug(f"Current route set to: %s", self.model.next_stage)

                if self.model.config.handle_session_inactivity:
                    session.save(session_id=session_id, key=SessionConstants.LAST_ACTIVITY_AT,
                                 data=datetime.now().isoformat())

        return response
