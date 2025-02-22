from pathlib import Path
from typing import Dict, Any

import ruamel.yaml

from pywce.modules import client, ISessionManager
from pywce.src.constants import TemplateTypeConstants, SessionConstants
from pywce.src.exceptions import ExtHandlerHookError, HookError, EngineException
from pywce.src.models import EngineConfig, WorkerJob, WhatsAppServiceModel, HookArg, ExternalHandlerResponse
from pywce.src.services import Worker, WhatsAppService, HookService
from pywce.src.utils import pywce_logger

_logger = pywce_logger(__name__)


class Engine:
    _TEMPLATES: Dict = {}
    _TRIGGERS: Dict = {}

    def __init__(self, config: EngineConfig):
        self.config: EngineConfig = config
        self.whatsapp = config.whatsapp

        self._load_resources()

    def _load_resources(self):
        self._TEMPLATES.clear()
        self._TRIGGERS.clear()

        yaml = ruamel.yaml.YAML()

        template_path = Path(self.config.templates_dir)
        trigger_path = Path(self.config.trigger_dir)

        if not template_path.is_dir() or not trigger_path.is_dir():
            raise EngineException("Template or trigger dir provided is not a valid directory")

        _logger.debug(f"Loading templates from dir: {template_path}")

        for template_file in template_path.glob("*.yaml"):
            with template_file.open("r", encoding="utf-8") as file:
                data = yaml.load(file)
                if data:
                    self._TEMPLATES.update(data)

        _logger.debug(f"Loading triggers from dir: {trigger_path}")
        for trigger_file in trigger_path.glob("*.yaml"):
            with trigger_file.open("r", encoding="utf-8") as file:
                data = yaml.load(file)
                if data:
                    self._TRIGGERS.update(data)

    def get_templates(self) -> Dict:
        return self._TEMPLATES

    def get_triggers(self) -> Dict:
        return self._TRIGGERS

    def verify_webhook(self, mode, challenge, token):
        return self.whatsapp.util.verify_webhook_verification_challenge(mode, challenge, token)

    def terminate_external_handler(self, recipient_id: str):
        user_session: ISessionManager = self.config.session_manager.session(session_id=recipient_id)
        has_ls_session = user_session.get(session_id=recipient_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)

        if has_ls_session is not None:
            user_session.evict(session_id=recipient_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
            _logger.debug("LS session terminated for: %s", recipient_id)

    async def ext_handler_respond(self, response: ExternalHandlerResponse):
        """
            Respond to user
        """
        user_session: ISessionManager = self.config.session_manager.session(session_id=response.recipient_id)
        has_ls_session = user_session.get(session_id=response.recipient_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)

        if has_ls_session is not None:
            # TODO: create template messages
            _template = {
                "type": "text",
                "message-id": response.reply_message_id,
                "message": response.message
            }

            service_model = WhatsAppServiceModel(
                template_type=TemplateTypeConstants.TEXT,
                template=_template,
                whatsapp=self.whatsapp,
                user=client.WaUser(wa_id=response.recipient_id),
                hook_arg=HookArg(user=client.WaUser(wa_id=response.recipient_id)),
            )

            whatsapp_service = WhatsAppService(model=service_model, validate_template=False)
            response = await whatsapp_service.send_message(handle_session=False, template=False)

            response_msg_id = self.whatsapp.util.get_response_message_id(response)

            _logger.debug("ExtHandler message responded with id: %s", response_msg_id)

            return response_msg_id

        raise ExtHandlerHookError(message="No active ExternalHandler session for user!")

    async def process_webhook(self, webhook_data: Dict[str, Any], webhook_headers: Dict[str, Any]):
        if self.whatsapp.config.enforce_security is True:
            if self.whatsapp.util.verify_webhook_payload(webhook_payload=webhook_data,
                                                         webhook_headers=webhook_headers) is False:
                _logger.warning("Invalid webhook payload")
                return

        if not self.whatsapp.util.is_valid_webhook_message(webhook_data):
            _logger.warning("Invalid webhook message: %s",
                            webhook_data if self.config.log_invalid_webhooks is True else "skipping..")
            return

        wa_user = self.whatsapp.util.get_wa_user(webhook_data)
        user_session: ISessionManager = self.config.session_manager.session(session_id=wa_user.wa_id)
        response_model = self.whatsapp.util.get_response_structure(webhook_data)

        # check if user has running external handler
        has_ext_session = user_session.get(session_id=wa_user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)

        if has_ext_session is None:
            worker = Worker(
                job=WorkerJob(
                    engine_config=self.config,
                    payload=response_model,
                    user=wa_user,
                    templates=self._TEMPLATES,
                    triggers=self._TRIGGERS,
                    session_manager=user_session
                )
            )
            await worker.work()

        else:
            if self.config.ext_handler_hook is not None:
                try:
                    # TEXT messages only supported
                    _arg = HookArg(
                        session_id=wa_user.wa_id,
                        session_manager=user_session,
                        user=wa_user,
                        user_input=response_model.body.get("body"),
                        additional_data={}
                    )

                    HookService.process_hook(
                        hook_dotted_path=self.config.ext_handler_hook,
                        hook_arg=_arg
                    )
                    return
                except HookError as e:
                    _logger.critical("Error processing external handler hook", exc_info=True)
                    raise ExtHandlerHookError(message=e.message)

            else:
                _logger.warning("No external handler hook provided, skipping..")
