from typing import Dict, Any

from pywce.modules import client, ISessionManager
from pywce.src.constants import TemplateTypeConstants, SessionConstants
from pywce.src.exceptions import ExtHandlerHookError, HookError, EngineInternalException
from pywce.src.models import EngineConfig, WorkerJob, WhatsAppServiceModel, HookArg, ExternalHandlerResponse
from pywce.src.services import Worker, WhatsAppService, HookService
from pywce.src.utils import pywce_logger

_logger = pywce_logger(__name__)


class Engine:
    def __init__(self, config: EngineConfig):
        self.config: EngineConfig = config
        self.whatsapp = config.whatsapp

        HookService.register_callable_global_hooks(self.config.global_pre_hooks, self.config.global_post_hooks)

    def verify_webhook(self, mode, challenge, token):
        return self.whatsapp.util.webhook_challenge(mode, challenge, token)

    def terminate_external_handler(self, recipient_id: str):
        """
            terminate external handler session for given recipient_id

            after termination, user messages will be handled by the normal template-driven approach
        """
        user_session: ISessionManager = self.config.session_manager.session(session_id=recipient_id)
        has_ext_handler_session = user_session.get(session_id=recipient_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)

        if has_ext_handler_session is not None:
            user_session.evict(session_id=recipient_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
            _logger.debug("External handler session terminated for: %s", recipient_id)

    async def ext_handler_respond(self, response: ExternalHandlerResponse):
        """
            helper method for external handler to send back response to user
        """
        user_session: ISessionManager = self.config.session_manager.session(session_id=response.recipient_id)
        has_ext_handler_session = user_session.get(session_id=response.recipient_id,
                                                   key=SessionConstants.EXTERNAL_CHAT_HANDLER)

        if has_ext_handler_session is not None:
            match response.typ:
                case TemplateTypeConstants.TEXT:
                    _template = {
                        "type": "text",
                        "message-id": response.reply_message_id,
                        "message": response.message
                    }

                case TemplateTypeConstants.BUTTON:
                    _template = {
                        "type": "button",
                        "message-id": response.reply_message_id,
                        "message": {
                            "title": response.title,
                            "body": response.message,
                            "buttons": response.options
                        }
                    }

                case TemplateTypeConstants.LIST:
                    _sections = {}

                    for option in response.options:
                        _sections[option["id"]] = {
                            "title": option["id"],
                            "description": option["description"]
                        }

                    _template = {
                        "type": "list",
                        "message-id": response.reply_message_id,
                        "message": {
                            "title": response.title,
                            "body": response.message,
                            "sections": {
                                response.title: _sections
                            }
                        }
                    }

                case _:
                    raise EngineInternalException("Type not supported for external handler")

            service_model = WhatsAppServiceModel(
                template_type=response.typ,
                template=_template,
                whatsapp=self.whatsapp,
                user=client.WaUser(wa_id=response.recipient_id),
                hook_arg=HookArg(
                    user=client.WaUser(wa_id=response.recipient_id),
                    session_id=response.recipient_id,
                    session_manager=user_session
                ),
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
                    storage=self.config.storage_manager,
                    session_manager=user_session
                )
            )
            await worker.work()

        else:
            if self.config.ext_handler_hook is not None:
                try:
                    _arg = HookArg(
                        session_id=wa_user.wa_id,
                        session_manager=user_session,
                        user=wa_user,
                        user_input=response_model,
                        additional_data={}
                    )

                    await HookService.process_hook(
                        hook_dotted_path=self.config.ext_handler_hook,
                        hook_arg=_arg
                    )
                    return
                except HookError as e:
                    _logger.critical("Error processing external handler hook", exc_info=True)
                    raise ExtHandlerHookError(message=e.message)

            else:
                _logger.warning("No external handler hook provided, skipping..")
