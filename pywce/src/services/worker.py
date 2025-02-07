from datetime import datetime
from random import randint
from time import time
from typing import List, Dict, Any, Tuple

from pywce.modules import ISessionManager, client
from pywce.src.constants import *
from pywce.src.exceptions import *
from pywce.src.models import WorkerJob, WhatsAppServiceModel, QuickButtonModel
from pywce.src.services import MessageProcessor, WhatsAppService
from pywce.src.utils import EngineUtil
from pywce.src.utils.engine_logger import pywce_logger

_logger = pywce_logger(__name__)


class Worker:
    """
        main engine worker class

        handles processing a single webhook request, process template
        and send request back to WhatsApp
    """

    def __init__(self, job: WorkerJob):
        self.job = job
        self.payload = job.payload
        self.user = job.user
        self.session_id = self.user.wa_id
        self.session: ISessionManager = self.job.session_manager

    def _get_message_queue(self) -> List:
        return self.session.get(session_id=self.session_id, key=SessionConstants.MESSAGE_HISTORY) or []

    def _append_message_to_queue(self):
        queue = self._get_message_queue()
        queue.append(self.user.msg_id)

        if len(queue) > EngineConstants.MESSAGE_QUEUE_COUNT:
            queue = queue[-EngineConstants.MESSAGE_QUEUE_COUNT:]

        self.session.save(session_id=self.session_id, key=SessionConstants.MESSAGE_HISTORY, data=queue)

    def _exists_in_queue(self) -> bool:
        queue_history = self._get_message_queue()
        return self.user.msg_id in list(set(queue_history))

    def _is_old_webhook(self) -> bool:
        webhook_time = datetime.fromtimestamp(float(self.user.timestamp))
        current_time = datetime.now()
        time_difference = abs((current_time - webhook_time).total_seconds())
        return time_difference > self.job.engine_config.webhook_timestamp_threshold_s

    def _check_authentication(self, current_template: Dict) -> None:
        if TemplateConstants.AUTHENTICATED in current_template:
            is_auth_set = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_SESSION)
            session_wa_id = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_MSISDN)
            logged_in_time = self.session.get(session_id=self.session_id, key=SessionConstants.AUTH_EXPIRE_AT)

            is_invalid = logged_in_time is None or is_auth_set is None or session_wa_id is None \
                         or EngineUtil.has_session_expired(logged_in_time) is True

            if is_invalid:
                raise EngineSessionException(
                    message="Your session has expired. Kindly login again to access our WhatsApp Services")

    def _inactivity_handler(self) -> bool:
        if self.job.engine_config.handle_session_inactivity is False: return False

        is_auth_set = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_SESSION)
        last_active = self.session.get(session_id=self.session_id, key=SessionConstants.LAST_ACTIVITY_AT)

        if is_auth_set:
            return EngineUtil.has_interaction_expired(last_active, self.job.engine_config.inactivity_timeout_min)
        return False

    def _checkpoint_handler(self, routes: Dict[str, Any], user_input: str = None,
                            is_from_trigger: bool = False) -> bool:
        """
        Check if a checkpoint is available in session. If so,

        Check if user input is `Retry` - only keyword response to trigger go-to-checkpoint logic
        :return: bool
        """

        _input = user_input or ''
        checkpoint = self.session.get(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT)
        dynamic_retry = self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)

        should_reroute_to_checkpoint = EngineConstants.RETRY_NAME_KEY not in routes \
                                       and _input.lower() == EngineConstants.RETRY_NAME_KEY.lower() \
                                       and checkpoint is not None \
                                       and dynamic_retry is not None \
                                       and is_from_trigger is False

        return should_reroute_to_checkpoint

    def _next_route_handler(self, msg_processor: MessageProcessor) -> str:
        if msg_processor.IS_FIRST_TIME: return self.job.engine_config.start_template_stage

        if self._inactivity_handler():
            raise EngineSessionException(
                message="You have been inactive for a while, to secure your account, kindly login again")

        # get possible next routes configured on template
        current_template_routes: Dict[str, Any] = msg_processor.CURRENT_TEMPLATE.get(TemplateConstants.ROUTES)

        # check for next route in last checkpoint
        if self._checkpoint_handler(current_template_routes, msg_processor.USER_INPUT[0],
                                    msg_processor.IS_FROM_TRIGGER):
            return self.session.get(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT)

        # check for next route in configured dynamic route if any
        if msg_processor.process_dynamic_route_hook() is not None:
            return msg_processor.process_dynamic_route_hook()

        # if from trigger, prioritize triggered stage
        if msg_processor.IS_FROM_TRIGGER:
            return msg_processor.CURRENT_STAGE

        # check for next route in configured template routes
        for _pattern, _route in current_template_routes.items():
            if EngineUtil.is_regex_input(_pattern):
                if msg_processor.USER_INPUT[0] is None:
                    # received an unprocessable input e.g. location-request / media message
                    # provide a dummy input that may match {"re:.*": "NEXT-STAGE"}
                    # this is to avoid any proper defined route that may match accidentally
                    _dummy_input = f"pywce.{randint(11, 1111)}"
                    if EngineUtil.is_regex_pattern_match(EngineUtil.extract_pattern(_pattern), _dummy_input):
                        return _route

                else:
                    if EngineUtil.is_regex_pattern_match(EngineUtil.extract_pattern(_pattern),
                                                         msg_processor.USER_INPUT[0]):
                        return _route

        # check for next route in template routes that match exact user input
        if msg_processor.USER_INPUT[0] in current_template_routes:
            return current_template_routes[msg_processor.USER_INPUT[0]]

        # at this point, user provided an invalid response then
        raise EngineResponseException(message="Invalid response, please try again", data=msg_processor.CURRENT_STAGE)

    def _hook_next_template_handler(self, msg_processor: MessageProcessor) -> Tuple[str, Dict]:
        """
        Handle next template to render to user

        Process all template hooks, pre-hooks & post-hooks

        :param msg_processor: MessageProcessor object
        :return:
        """
        if self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY) is None:
            msg_processor.process_post_hooks()

        next_template_stage = self._next_route_handler(msg_processor)

        if next_template_stage not in self.job.templates:
            raise EngineInternalException(
                message=f"Next stage route: {next_template_stage} not found in templates context map")

        next_template = self.job.templates.get(next_template_stage)

        # check if next template requires user to be authenticated before processing
        self._check_authentication(next_template)

        # process all `next template` pre hooks
        msg_processor.process_pre_hooks(next_template)

        return next_template_stage, next_template

    async def send_quick_btn_message(self, payload: QuickButtonModel) -> None:
        """
        Helper method to send a quick button to the user
        without handling engine session logic
        :return:
        """
        _client = self.job.engine_config.whatsapp

        _template = {
            "type": "button",
            "message-id": payload.message_id,
            "message": {
                "title": payload.title,
                "body": payload.message,
                "footer": payload.footer,
                "buttons": payload.buttons
            }
        }

        service_model = WhatsAppServiceModel(
            template_type=TemplateTypeConstants.BUTTON,
            template=_template,
            whatsapp=_client,
            user=self.user
        )

        whatsapp_service = WhatsAppService(model=service_model, validate_template=False)
        response = await whatsapp_service.send_message(handle_session=False, template=False)

        response_msg_id = _client.util.get_response_message_id(response)

        _logger.debug("Quick button message responded with id: %s", response_msg_id)

    async def _runner(self):
        processor = MessageProcessor(data=self.job)
        processor.setup()

        next_stage, next_template = self._hook_next_template_handler(processor)

        _logger.info("Next template stage: %s", next_stage)

        service_model = WhatsAppServiceModel(
            template_type=TEMPLATE_TYPE_MAPPING.get(next_template.get(TemplateConstants.TEMPLATE_TYPE)),
            template=next_template,
            whatsapp=processor.whatsapp,
            user=self.user,
            next_stage=next_stage,
            hook_arg=processor.HOOK_ARG,
            tag_on_reply=self.job.engine_config.tag_on_reply,
            read_receipts=self.job.engine_config.read_receipts,
            handle_session_activity=self.job.engine_config.handle_session_inactivity
        )

        whatsapp_service = WhatsAppService(model=service_model)
        await whatsapp_service.send_message()

        processor.IS_FROM_TRIGGER = False

    async def work(self):
        """
        Handles every webhook request

        :return: None
        """

        if self._is_old_webhook():
            _logger.warning(f"Skipping old webhook request. {self.payload.body} Discarding...")
            return

        if self.job.payload.typ == client.MessageTypeEnum.UNKNOWN or self.job.payload.typ == client.MessageTypeEnum.UNSUPPORTED:
            _logger.warning(f"Received unknown | unsupported message: {self.user.wa_id}")
            return

        if self.job.engine_config.handle_session_queue:
            if self._exists_in_queue():
                _logger.warning(f"Duplicate message found: {self.payload.body}")
                return

        last_debounce_timestamp = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE)
        current_time = int(time() * 1000)
        no_debounce = last_debounce_timestamp is None or \
                      current_time - last_debounce_timestamp >= self.job.engine_config.debounce_timeout_ms

        if no_debounce is True:
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE, data=current_time)

        else:
            _logger.warning("Message ignored due to debounce..")
            return

        if self.job.engine_config.handle_session_queue:
            self._append_message_to_queue()

        try:
            await self._runner()

            self.session.evict(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_MSG_ID, data=self.user.msg_id)

        except TemplateRenderException as e:
            _logger.error("Failed to render template: " + e.message)

            btn = QuickButtonModel(
                title="Message",
                message="Failed to process message",
                buttons=[EngineConstants.DEFAULT_RETRY_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
            )

            await self.send_quick_btn_message(payload=btn)

            return

        except EngineResponseException as e:
            _logger.error("EngineResponse: " + e.message)

            btn = QuickButtonModel(
                title="Message",
                message=f"{e.message}\n\n. You may click the Menu button to return to Menu",
                buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
            )

            await self.send_quick_btn_message(payload=btn)

            return

        except UserSessionValidationException as e:
            _logger.critical("Ambiguous session mismatch encountered with %s" % self.user.wa_id)
            _logger.error(e.message)

            btn = QuickButtonModel(
                title="Message",
                message="Failed to understand something on my end.\n\nCould not process message.",
                buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME]
            )

            await self.send_quick_btn_message(payload=btn)

            return

        except EngineSessionException as e:
            _logger.warning("Session expired | inactive for: %s. Clearing data" % self.user.wa_id)

            # clear all user session data
            self.session.clear(session_id=self.user.wa_id)

            btn = QuickButtonModel(
                title="Security Check 🔐",
                message=e.message,
                footer="Session Expired",
                buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME]
            )

            await self.send_quick_btn_message(payload=btn)

            return

        except EngineInternalException as e:
            _logger.critical(e.message)
            return
