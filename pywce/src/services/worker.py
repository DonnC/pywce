import logging
from datetime import datetime
from time import time
from typing import List, Tuple

from pywce.modules import ISessionManager, client
from pywce.src.constants import *
from pywce.src.exceptions import *
from pywce.src.models import HookArg, WorkerJob, WhatsAppServiceModel
from pywce.src.services import MessageProcessor, WhatsAppService
from pywce.src.templates import ButtonTemplate, EngineTemplate, ButtonMessage, EngineRoute, FlowTemplate, \
    RequestLocationTemplate, MediaTemplate, CtaTemplate, TemplateTemplate, ProductTemplate, \
    MultiProductTemplate
from pywce.src.utils.engine_util import EngineUtil

logger = logging.getLogger(__name__)


class Worker:
    """
        main engine worker class

        handles processing a single webhook request, process templates
        and send request back to WhatsApp
    """

    def __init__(self, job: WorkerJob):
        self.job = job
        self.payload = job.payload
        self.user = job.user
        self.session_id = self.user.wa_id
        self.session: ISessionManager = self.job.engine_config.session_manager.session(self.session_id)

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

    def _check_authentication(self, current_template: EngineTemplate) -> None:
        if current_template.authenticated and self.job.engine_config.has_auth:
            is_auth_set = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_SESSION)
            logged_in_time = self.session.get(session_id=self.session_id, key=SessionConstants.AUTH_EXPIRE_AT)

            is_invalid = logged_in_time is None or is_auth_set is None \
                         or EngineUtil.has_session_expired(logged_in_time) is True

            if is_invalid:
                raise EngineSessionException(
                    message="Your session has expired. Kindly login again to access our WhatsApp Services")

    def _inactivity_handler(self) -> bool:
        if self.job.engine_config.handle_session_inactivity is False: return False

        is_auth_set = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_SESSION)
        last_active = self.session.get(session_id=self.session_id, key=SessionConstants.LAST_ACTIVITY_AT)

        if self.job.engine_config.has_auth and is_auth_set is not None:
            return EngineUtil.has_interaction_expired(last_active, self.job.engine_config.inactivity_timeout_min)
        return False

    def _checkpoint_handler(self, routes: List[EngineRoute], user_input: str = None,
                            is_from_trigger: bool = False) -> bool:
        """
        Check if a checkpoint is available in session. If so,

        Check if user input is `Retry` - only keyword response to trigger go-to-checkpoint logic
        :return: bool


        boolean gotoCheckpoint = !this.templateHasKey(currentStageRoutes, EngineConstants.RETRY_NAME)
                && this.currentStageUserInput.toString().equalsIgnoreCase(EngineConstants.RETRY_NAME)
                && checkpoint != null
                && this.session.get(this.sessionId, SessionConstants.SESSION_DYNAMIC_RETRY_KEY) != null
                && !this.isFromTrigger;
        """

        _input = user_input or ''
        checkpoint = self.session.get(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT)
        dynamic_retry = self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)

        route_has_retry_input = False
        user_input_is_retry = _input.strip().lower() == EngineConstants.RETRY_NAME_KEY.lower()

        for r in routes:
            if str(r.user_input).lower() == EngineConstants.RETRY_NAME_KEY.lower():
                route_has_retry_input = True
                break

        should_reroute_to_checkpoint = route_has_retry_input is False and checkpoint is not None \
                                       and dynamic_retry is not None and user_input_is_retry is True \
                                       and is_from_trigger is False

        return should_reroute_to_checkpoint

    def _next_route_handler(self, msg_processor: MessageProcessor) -> str:
        _user_input = msg_processor.USER_INPUT[0]

        if msg_processor.IS_FIRST_TIME: return self.job.engine_config.start_template_stage

        if self._inactivity_handler():
            raise EngineSessionException(
                message="You have been inactive for a while, to secure your account, kindly login again")

        # get possible next common configured on templates
        current_template_routes = msg_processor.CURRENT_TEMPLATE.routes

        # check for next route in last checkpoint
        if self._checkpoint_handler(current_template_routes, _user_input,
                                    msg_processor.IS_FROM_TRIGGER):
            return self.session.get(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT)

        # check for next route in configured dynamic route if any
        _has_dynamic_route = msg_processor.process_dynamic_route_hook()
        if _has_dynamic_route is not None:
            return _has_dynamic_route

        # if from trigger, prioritize triggered stage
        if msg_processor.IS_FROM_TRIGGER:
            return msg_processor.CURRENT_STAGE

        # if its 1 of the unprocessable templates, just take the next route
        is_route_unprocessable = isinstance(msg_processor.CURRENT_TEMPLATE, FlowTemplate) or \
                                 isinstance(msg_processor.CURRENT_TEMPLATE, RequestLocationTemplate) or \
                                 isinstance(msg_processor.CURRENT_TEMPLATE, MediaTemplate) or \
                                 isinstance(msg_processor.CURRENT_TEMPLATE, CtaTemplate) or \
                                 isinstance(msg_processor.CURRENT_TEMPLATE, TemplateTemplate) or \
                                 isinstance(msg_processor.CURRENT_TEMPLATE, ProductTemplate) or \
                                 isinstance(msg_processor.CURRENT_TEMPLATE, MultiProductTemplate)

        if is_route_unprocessable:
            return current_template_routes[0].next_stage

        # check for next route in configured templates common
        for trigger in current_template_routes:
            if EngineUtil.has_triggered(trigger, _user_input):
                return trigger.next_stage

        # at this point, user provided an invalid response then
        raise EngineResponseException(message="Invalid response, please try again", data=msg_processor.CURRENT_STAGE)

    def _hook_next_template_handler(self, msg_processor: MessageProcessor) -> Tuple[str, EngineTemplate]:
        """
        Handle next templates to render to user

        Process all templates hooks, pre-hooks & post-hooks

        :param msg_processor: MessageProcessor object
        :return:
        """
        if self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY) is None:
            msg_processor.process_post_hooks()

        next_template_stage = self._next_route_handler(msg_processor)

        next_template = self.job.engine_config.storage_manager.get(next_template_stage)

        # check if next templates requires user to be authenticated before processing
        self._check_authentication(next_template)

        # process all `next templates` pre hooks
        msg_processor.process_pre_hooks(next_template)

        return next_template_stage, next_template

    def send_quick_btn_message(self, btn_template: ButtonTemplate):
        """
        Helper method to send a quick button to the user
        without handling engine session logic
        :return:
        """
        _client = self.job.engine_config.whatsapp

        service_model = WhatsAppServiceModel(
            config=self.job.engine_config,
            template=btn_template,
            hook_arg=HookArg(user=self.user, session_id=self.user.wa_id, user_input=None)
        )

        whatsapp_service = WhatsAppService(model=service_model)
        response = whatsapp_service.send_message(handle_session=False, template=False)

        response_msg_id = _client.util.get_response_message_id(response)

        logger.debug("Quick button message responded with id: %s", response_msg_id)

        return response_msg_id

    def _runner(self):
        processor = MessageProcessor(data=self.job)
        processor.setup()

        next_stage, next_template = self._hook_next_template_handler(processor)

        logger.debug("Next templates stage: %s", next_stage)

        service_model = WhatsAppServiceModel(
            config=self.job.engine_config,
            template=next_template,
            next_stage=next_stage,
            hook_arg=processor.HOOK_ARG
        )

        whatsapp_service = WhatsAppService(model=service_model)
        whatsapp_service.send_message()

        processor.IS_FROM_TRIGGER = False

    def work(self):
        """
        Handles every webhook request

        :return: None
        """

        if self._is_old_webhook():
            logger.warning(f"Skipping old webhook request. %s Discarding...", self.payload.body)
            return

        if self.job.payload.typ == client.MessageTypeEnum.UNKNOWN or \
                self.job.payload.typ == client.MessageTypeEnum.UNSUPPORTED:
            logger.warning(f"Received unknown | unsupported message: %s", self.user.wa_id)
            return

        if self.job.engine_config.handle_session_queue:
            if self._exists_in_queue():
                logger.warning(f"Duplicate message found: %s", self.payload.body)
                return

        last_debounce_timestamp = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE)
        current_time = int(time() * 1000)
        no_debounce = last_debounce_timestamp is None or \
                      current_time - last_debounce_timestamp >= self.job.engine_config.debounce_timeout_ms

        if no_debounce is True:
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE, data=current_time)

        else:
            logger.warning("Message ignored due to debounce..")
            return

        if self.job.engine_config.handle_session_queue:
            self._append_message_to_queue()

        try:
            self._runner()

            self.session.evict(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_MSG_ID, data=self.user.msg_id)

        except TemplateRenderException as e:
            logger.error("Failed to render templates: %s", e.message)

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body="Failed to process message",
                    buttons=[EngineConstants.DEFAULT_RETRY_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
                ),
                routes=[]
            )

            self.send_quick_btn_message(btn_template=btn)

            return

        except HookException as e:
            logger.error(f"HookException exc, message: %s, data: %s", e.message, e.data)

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body=e.message,
                    buttons=[EngineConstants.DEFAULT_RETRY_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
                ),
                routes=[]
            )

            self.send_quick_btn_message(btn_template=btn)

            return

        except EngineResponseException as e:
            logger.error(f"EngineResponse exc, message: %s, data: %s", e.message, e.data)

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body=f"{e.message}\n\nYou may click the Menu button to return to Menu",
                    buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
                ),
                routes=[]
            )

            self.send_quick_btn_message(btn_template=btn)

            return

        except UserSessionValidationException as e:
            logger.error("Ambiguous session mismatch encountered with %s", self.user.wa_id)
            logger.error("%s", e.message)

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body="Failed to understand something on my end.\n\nCould not process message.",
                    buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME]
                ),
                routes=[]
            )

            self.send_quick_btn_message(btn_template=btn)

            return

        except EngineSessionException as e:
            logger.error(f"Session expired | inactive for: %s. Clearing data", self.user.wa_id)

            # clear all user session data
            self.session.clear(session_id=self.user.wa_id)

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Security Check 🔐",
                    body=e.message,
                    footer="Session Expired",
                    buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME]
                ),
                routes=[]
            )

            self.send_quick_btn_message(btn_template=btn)

            return

        except EngineInternalException as e:
            logger.error(f"Message: %s, data: %s", e.message, e.data)
            return
