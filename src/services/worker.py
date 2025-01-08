from datetime import datetime
from time import time
from typing import List, Dict, Any

from engine_logger import get_engine_logger
from modules.session import ISessionManager
from modules.whatsapp import MessageTypeEnum
from src.constants.engine import EngineConstants
from src.constants.session import SessionConstants
from src.constants.template import TemplateConstants
from src.exceptions import TemplateRenderException, UserSessionValidationException, EngineResponseException, \
    EngineInternalException
from src.models import WorkerJob
from src.services.message_processor import MessageProcessor
from src.utils.engine_util import EngineUtil


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

        self.session: ISessionManager = job.engine_config.session_manager.session(self.session_id)
        self.logger = get_engine_logger(__name__)

    def __get_message_queue__(self) -> List:
        return self.session.get(session_id=self.session_id, key=SessionConstants.MESSAGE_HISTORY) or []

    def __append_message_to_queue__(self):
        queue = self.__get_message_queue__()
        queue.append(self.user.msg_id)

        if len(queue) > EngineConstants.MESSAGE_QUEUE_COUNT:
            self.logger.warning("Message queue limit reached, applying FIFO...")
            queue = queue[-EngineConstants.MESSAGE_QUEUE_COUNT:]

        self.session.save(session_id=self.session_id, key=SessionConstants.MESSAGE_HISTORY, data=queue)

    def __exists_in_queue__(self) -> bool:
        queue_history = self.__get_message_queue__()
        return self.user.msg_id in list(set(queue_history))

    def __is_old_webhook__(self) -> bool:
        webhook_time = datetime.fromtimestamp(float(self.user.timestamp))
        current_time = datetime.now()
        time_difference = abs((current_time - webhook_time).total_seconds())
        return time_difference > self.job.engine_config.webhook_timestamp_threshold_s

    def __check_authentication__(self, template: Dict) -> None:
        if TemplateConstants.AUTHENTICATED in template:
            is_auth_set = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_SESSION)
            session_wa_id = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_MSISDN)
            logged_in_time = self.session.get(session_id=self.session_id, key=SessionConstants.AUTH_EXPIRE_AT)

            is_invalid = logged_in_time is None or is_auth_set is None or session_wa_id is None or EngineUtil.has_session_expired(
                logged_in_time) is True

            if is_invalid:
                raise UserSessionValidationException(
                    message="Your session has expired. Kindly login again to access our WhatsApp Services")

    def __inactivity_handler__(self) -> bool:
        if self.job.engine_config.handle_session_inactivity is False: return False

        is_auth_set = self.session.get(session_id=self.session_id, key=SessionConstants.VALID_AUTH_SESSION)
        last_active = self.session.get(session_id=self.session_id, key=SessionConstants.LAST_ACTIVITY_AT)

        if is_auth_set:
            return EngineUtil.has_interaction_expired(last_active, self.job.engine_config.inactivity_timeout_min)
        return False

    def __checkpoint_handler__(self, routes: Dict[str, Any], user_input: str = None,
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
                                       and user_input.lower() == EngineConstants.RETRY_NAME_KEY.name.lower() \
                                       and checkpoint is not None \
                                       and dynamic_retry is not None \
                                       and is_from_trigger is False

        return should_reroute_to_checkpoint

    def __next_route_handler__(self, msg_processor: MessageProcessor) -> str:
        if msg_processor.IS_FIRST_TIME: return self.job.engine_config.start_template_stage

        if self.__inactivity_handler__():
            raise UserSessionValidationException(
                message="You have been inactive for a while, to secure your account, kindly login again")

        # get possible next routes configured on template
        current_template_routes: Dict[str, Any] = msg_processor.CURRENT_TEMPLATE.get(TemplateConstants.ROUTES)

        # check for next route in last checkpoint
        if self.__checkpoint_handler__(current_template_routes, msg_processor.USER_INPUT[0],
                                       msg_processor.IS_FROM_TRIGGER):
            return self.session.get(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT)

        # check for next route in configured dynamic route if any
        if msg_processor.process_dynamic_route_hook() is not None:
            return msg_processor.process_dynamic_route_hook()

        # check for next route in configured template routes
        for _pattern, _route in current_template_routes.items():
            if EngineUtil.is_regex_input(_pattern):
                if EngineUtil.is_regex_pattern_match(EngineUtil.extract_pattern(_pattern), msg_processor.USER_INPUT[0]):
                    return _route

        # check for next route in template routes that match exact user input
        if msg_processor.USER_INPUT[0] in current_template_routes:
            return current_template_routes[msg_processor.USER_INPUT[0]]

        # at this point, user provided an invalid response then
        raise EngineResponseException(message="Invalid response, please try again", data=msg_processor.CURRENT_STAGE)

    def __hook_next_template_handler__(self, msg_processor: MessageProcessor) -> None:
        """
        Handle next template to render to user

        Process all template hooks, pre-hooks & post-hooks

        :param msg_processor: MessageProcessor object
        :return:
        """
        if self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY) is None:
            msg_processor.process_post_hooks()

        next_template_stage = self.__next_route_handler__(msg_processor)

        if next_template_stage not in self.job.templates:
            raise EngineInternalException(
                message=f"Next stage route: {next_template_stage} not found in templates context map")

        next_template = self.job.templates.get(next_template_stage)

        # check if next template requires user to be authenticated before processing
        self.__check_authentication__(next_template)

        # process all `next template` pre hooks
        msg_processor.process_pre_hooks(next_template)

    def __processor__(self):
        processor = MessageProcessor(data=self.job)
        processor.setup()

        self.__hook_next_template_handler__(processor)

        # TODO: process payload generation and send response back to whatsapp

        processor.IS_FROM_TRIGGER = False

    def work(self):
        """
        Handles every webhook request

        :return: None
        """

        if self.__is_old_webhook__():
            self.logger.info(f"Skipping webhook request. {self.payload.body} Discarding...")
            return

        if self.job.payload.model == MessageTypeEnum.UNKNOWN or self.job.payload.model == MessageTypeEnum.UNSUPPORTED:
            self.logger.warning(f"Received unknown | unsupported message: {self.user.wa_id}")
            return

        if self.job.engine_config.handle_session_queue:
            if self.__exists_in_queue__():
                self.logger.warning(f"Duplicate message found: {self.payload.body}")
                return

        last_debounce_timestamp = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE)
        current_time = int(time() * 1000)

        if last_debounce_timestamp is None or current_time - last_debounce_timestamp >= self.job.engine_config.debounce_timeout_ms:
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE, data=current_time)

        else:
            self.logger.warning("Message ignored due to debounce..")
            return

        if self.job.engine_config.handle_session_queue:
            self.__append_message_to_queue__()

        try:
            self.__processor__()

            self.session.evict(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_MSG_ID, data=self.user.msg_id)

        except TemplateRenderException as e:
            self.logger.error("Failed to render template: " + e.message)
            # TODO: generate and send a button message
            #       message: Failed to process your message
            #       buttons: [Retry, Report]
            return
