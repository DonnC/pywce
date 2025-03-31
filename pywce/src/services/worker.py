from datetime import datetime
from random import randint
from time import time
from typing import List, Tuple

from pywce.modules import ISessionManager, client
from pywce.src.constants import *
from pywce.src.exceptions import *
from pywce.src.models import HookArg
from pywce.src.models import WorkerJob, WhatsAppServiceModel
from pywce.src.services import MessageProcessor, WhatsAppService
from pywce.src.templates import ButtonTemplate, EngineTemplate, ButtonMessage, EngineRoute
from pywce.src.utils.engine_util import EngineUtil


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
        if current_template.authenticated is True:
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

    def _checkpoint_handler(self, routes: List[EngineRoute], user_input: str = None,
                            is_from_trigger: bool = False) -> bool:
        """
        Check if a checkpoint is available in session. If so,

        Check if user input is `Retry` - only keyword response to trigger go-to-checkpoint logic
        :return: bool
        """

        _input = user_input or ''
        checkpoint = self.session.get(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT)
        dynamic_retry = self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)

        has_retry_input = False

        for r in routes:
            if str(r.user_input).upper() == EngineConstants.RETRY_NAME_KEY.upper():
                if _input.strip().lower() == EngineConstants.RETRY_NAME_KEY.lower():
                    has_retry_input = True

        should_reroute_to_checkpoint = has_retry_input and checkpoint is not None \
                                       and dynamic_retry is not None \
                                       and is_from_trigger is False

        return should_reroute_to_checkpoint

    async def _next_route_handler(self, msg_processor: MessageProcessor) -> str:
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
        _has_dynamic_route = await msg_processor.process_dynamic_route_hook()
        if _has_dynamic_route is not None:
            return _has_dynamic_route

        # if from trigger, prioritize triggered stage
        if msg_processor.IS_FROM_TRIGGER:
            return msg_processor.CURRENT_STAGE

        # check for next route in configured templates common
        for trigger in current_template_routes:
            if _user_input is None:
                # received an unprocessable input e.g. location-request / media message
                # provide a dummy input that may match {"re:.*": "NEXT-STAGE"}
                # this is to avoid any proper defined route that may match accidentally
                _dummy_input = f"pywce.{randint(11, 1111)}"
                if EngineUtil.has_triggered(trigger, _dummy_input):
                    return trigger.next_stage

            else:
                if EngineUtil.has_triggered(trigger, _user_input):
                    return trigger.next_stage

        # at this point, user provided an invalid response then
        raise EngineResponseException(message="Invalid response, please try again", data=msg_processor.CURRENT_STAGE)

    async def _hook_next_template_handler(self, msg_processor: MessageProcessor) -> Tuple[str, EngineTemplate]:
        """
        Handle next templates to render to user

        Process all templates hooks, pre-hooks & post-hooks

        :param msg_processor: MessageProcessor object
        :return:
        """
        if self.session.get(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY) is None:
            await msg_processor.process_post_hooks()

        next_template_stage = await self._next_route_handler(msg_processor)

        next_template = self.job.engine_config.storage_manager.get(next_template_stage)

        # check if next templates requires user to be authenticated before processing
        self._check_authentication(next_template)

        # process all `next templates` pre hooks
        await msg_processor.process_pre_hooks(next_template)

        return next_template_stage, next_template

    async def send_quick_btn_message(self, btn_template: ButtonTemplate):
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
        response = await whatsapp_service.send_message(handle_session=False, template=False)

        response_msg_id = _client.util.get_response_message_id(response)

        self.job.engine_config.logger.log("Quick button message responded with id: %s", response_msg_id)

        return response_msg_id

    async def _runner(self):
        processor = MessageProcessor(data=self.job)
        processor.setup()

        next_stage, next_template = await self._hook_next_template_handler(processor)

        self.job.engine_config.logger.log("Next templates stage: " + next_stage)

        service_model = WhatsAppServiceModel(
            config=self.job.engine_config,
            template=next_template,
            next_stage=next_stage,
            hook_arg=processor.HOOK_ARG
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
            self.job.engine_config.logger.log(f"Skipping old webhook request. {self.payload.body} Discarding...",
                                              level="WARNING")
            return

        if self.job.payload.typ == client.MessageTypeEnum.UNKNOWN or \
                self.job.payload.typ == client.MessageTypeEnum.UNSUPPORTED:
            self.job.engine_config.logger.log(f"Received unknown | unsupported message: {self.user.wa_id}",
                                              level="WARNING")
            return

        if self.job.engine_config.handle_session_queue:
            if self._exists_in_queue():
                self.job.engine_config.logger.log(f"Duplicate message found: {self.payload.body}", level="WARNING")
                return

        last_debounce_timestamp = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE)
        current_time = int(time() * 1000)
        no_debounce = last_debounce_timestamp is None or \
                      current_time - last_debounce_timestamp >= self.job.engine_config.debounce_timeout_ms

        if no_debounce is True:
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_DEBOUNCE, data=current_time)

        else:
            self.job.engine_config.logger.log("Message ignored due to debounce..", level="WARNING")
            return

        if self.job.engine_config.handle_session_queue:
            self._append_message_to_queue()

        try:
            await self._runner()

            self.session.evict(session_id=self.session_id, key=SessionConstants.DYNAMIC_RETRY)
            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_MSG_ID, data=self.user.msg_id)

        except TemplateRenderException as e:
            self.job.engine_config.logger.log("Failed to render templates: " + e.message, level="ERROR")

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body="Failed to process message",
                    buttons=[EngineConstants.DEFAULT_RETRY_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
                ),
                routes=[]
            )

            await self.send_quick_btn_message(btn_template=btn)

            return

        except EngineResponseException as e:
            self.job.engine_config.logger.log(f"EngineResponse exc, message: {e.message}, data: {e.data}",
                                              level="ERROR")

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body=f"{e.message}\n\nYou may click the Menu button to return to Menu",
                    buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME, EngineConstants.DEFAULT_REPORT_BTN_NAME]
                ),
                routes=[]
            )

            await self.send_quick_btn_message(btn_template=btn)

            return

        except UserSessionValidationException as e:
            self.job.engine_config.logger.log("Ambiguous session mismatch encountered with " + self.user.wa_id,
                                              level="ERROR")
            self.job.engine_config.logger.log(e.message, level="ERROR")

            btn = ButtonTemplate(
                message=ButtonMessage(
                    title="Message",
                    body="Failed to understand something on my end.\n\nCould not process message.",
                    buttons=[EngineConstants.DEFAULT_MENU_BTN_NAME]
                ),
                routes=[]
            )

            await self.send_quick_btn_message(btn_template=btn)

            return

        except EngineSessionException as e:
            self.job.engine_config.logger.log(f"Session expired | inactive for: {self.user.wa_id}. Clearing data",
                                              level="ERROR")

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

            await self.send_quick_btn_message(btn_template=btn)

            return

        except EngineInternalException as e:
            self.job.engine_config.logger.log(f"Message: {e.message}, data: {e.data}", level="ERROR")
            return
