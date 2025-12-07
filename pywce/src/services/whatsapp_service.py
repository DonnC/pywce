import logging
from datetime import datetime as dtime
from typing import Dict, Any

import pywce.src.templates as templates
from pywce.modules import history
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
        wa_util = self.model.config.whatsapp.util
        payload: Dict[str, Any] = self._processor.payload(template)
        _tpl = self._processor.template

        # history
        _history_content = "<message>"
        _history_metadata = None

        is_interactive: bool = isinstance(_tpl, templates.ButtonTemplate) or \
                               isinstance(_tpl, templates.CtaTemplate) or \
                               isinstance(_tpl, templates.CatalogTemplate) or \
                               isinstance(_tpl, templates.ProductTemplate) or \
                               isinstance(_tpl, templates.MultiProductTemplate) or \
                               isinstance(_tpl, templates.ListTemplate) or \
                               isinstance(_tpl, templates.FlowTemplate)

        if is_interactive:
            response = self.model.config.whatsapp.send_interactive(**payload)
            _history_content = _tpl.message.body
            _history_metadata = _tpl.message.model_dump_json()

        elif isinstance(_tpl, templates.TextTemplate):
            response = self.model.config.whatsapp.send_message(**payload)
            _history_content = _tpl.message
            _history_metadata = None

        elif isinstance(_tpl, templates.TemplateTemplate):
            response = self.model.config.whatsapp.send_template(**payload)
            _history_content = _tpl.message.name
            _history_metadata = _tpl.message.language

        elif isinstance(_tpl, templates.MediaTemplate):
            response = self.model.config.whatsapp.send_media(**payload)
            _history_content = _tpl.message.kind
            _history_metadata = _tpl.message.model_dump_json()

        elif isinstance(_tpl, templates.LocationTemplate):
            response = self.model.config.whatsapp.send_location(**payload)
            _history_content = f"({_tpl.message.lat}, {_tpl.message.lon})"
            _history_metadata = _tpl.message.model_dump_json()

        elif isinstance(_tpl, templates.RequestLocationTemplate):
            response = self.model.config.whatsapp.request_location(**payload)
            _history_content = _tpl.message
            _history_metadata = None

        else:
            raise EngineInternalException(
                message="Unsupported message type for payload generation",
                data=f"Stage: {self.model.next_stage} | Type: {_tpl.__class__.__name__}"
            )

        req_success = wa_util.was_request_successful(self.model.hook_arg.user.wa_id, response)
        dnow = dtime.now().isoformat()

        if template or req_success:
            session = self.model.hook_arg.session_manager
            session_id = self.model.hook_arg.user.wa_id
            current_stage = session.get(session_id=session_id, key=SessionConstants.CURRENT_STAGE)

            if self.model.config.history_manager:
                history_entry = history.History(
                    role="bot",
                    message_type=_tpl.kind,
                    content=_history_content,
                    metadata=_history_metadata,
                    timestamp=dnow,
                    stage=current_stage
                )
                self.model.config.history_manager.log_message(session_id, history_entry)

            if handle_session:
                session.save(session_id=session_id, key=SessionConstants.PREV_STAGE, data=current_stage)
                session.save(session_id=session_id, key=SessionConstants.CURRENT_STAGE, data=self.model.next_stage)

                logger.debug(f"Current route set to: %s", self.model.next_stage)

                if self.model.config.handle_session_inactivity:
                    session.save(session_id=session_id, key=SessionConstants.LAST_ACTIVITY_AT, data=dnow)

        return response
