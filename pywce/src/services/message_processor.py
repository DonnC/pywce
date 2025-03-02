from typing import Dict, Tuple, Any, Union

from pywce.modules import ISessionManager, client
from pywce.src.constants import EngineConstants, SessionConstants, TemplateConstants
from pywce.src.exceptions import EngineInternalException, EngineResponseException
from pywce.src.models import WorkerJob, HookArg
from pywce.src.services import HookService
from pywce.src.utils import EngineUtil
from pywce.src.utils.engine_logger import pywce_logger


class MessageProcessor:
    """
        Main message processor class

        Processes current message against template
        Processes all template hooks
    """
    CURRENT_TEMPLATE: Dict
    CURRENT_STAGE: str
    HOOK_ARG: HookArg
    IS_FIRST_TIME: bool = False
    IS_FROM_TRIGGER: bool = False

    # (input: str, data: dict)
    USER_INPUT: Tuple[Any, Any]

    def __init__(self, data: WorkerJob):
        self.data = data
        self.user = data.user
        self.config = data.engine_config
        self.whatsapp = data.engine_config.whatsapp
        self.payload = data.payload

        self.session_id = self.user.wa_id
        self.session: ISessionManager = self.config.session_manager.session(session_id=self.session_id)

        self.logger = pywce_logger(__name__)

    def _is_stage_in_repository(self, template_stage: str):
        return template_stage in self.data.templates

    def _get_stage_template(self, template_stage_name: str) -> Dict:
        tpl = self.data.templates.get(template_stage_name)
        if tpl is None:
            raise EngineInternalException(message=f"Template {template_stage_name} not found")
        return tpl

    def _get_current_template(self) -> None:
        current_stage_in_session = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE)

        if current_stage_in_session is None:
            self.CURRENT_STAGE = self.config.start_template_stage

            # assume user is new or session cleared
            if self._is_stage_in_repository(self.CURRENT_STAGE) is False:
                raise EngineInternalException(message="Configured start stage does not exist",
                                              data=self.CURRENT_STAGE)

            self.CURRENT_TEMPLATE = self._get_stage_template(self.CURRENT_STAGE)
            self.IS_FIRST_TIME = True

            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE, data=self.CURRENT_STAGE)
            self.session.save(session_id=self.session_id, key=SessionConstants.PREV_STAGE, data=self.CURRENT_STAGE)
            return

        if self._is_stage_in_repository(current_stage_in_session) is False:
            raise EngineInternalException(message="Template stage not found in template context map",
                                          data=current_stage_in_session)

        self.CURRENT_STAGE = current_stage_in_session
        self.CURRENT_TEMPLATE = self._get_stage_template(current_stage_in_session)

    def _check_if_trigger(self, possible_trigger_input: str = None) -> None:
        if possible_trigger_input is None:
            return

        for _stage, _pattern in self.data.triggers.items():
            if EngineUtil.is_regex_input(_pattern):
                if EngineUtil.is_regex_pattern_match(EngineUtil.extract_pattern(_pattern), possible_trigger_input):
                    if self._is_stage_in_repository(_stage) is False:
                        raise EngineInternalException(
                            message="Triggered template stage not found in template context map",
                            data=_stage
                        )

                    self.CURRENT_TEMPLATE = self._get_stage_template(_stage)
                    self.CURRENT_STAGE = _stage
                    self.IS_FROM_TRIGGER = True
                    self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE,
                                      data=self.CURRENT_STAGE)
                    self.logger.debug("Template change from trigger. Stage: " + _stage)
                    return

        # TODO: check if current msg id is null, throw Ambiguous old webhook exc

    def _get_message_body(self) -> None:
        """
        Extracts message body from webhook

        For type that cannot be processed easily e.g. MEDIA, LOCATION_REQUEST & FLOW
        the raw response data will be available under `USER_INPUT[1]` & `HookArg.additional_data` in hooks.

        For normal text messages & or buttons - the user selection or input will be available in `USER_INPUT[0]` &
        `HookArg.user_input` in hooks.

        If the resulting `USER_INPUT[0]` is None -> it signifies that user message cannot be processed e.g. Image

        Returns:
            None
        """

        match self.payload.typ:
            case client.MessageTypeEnum.TEXT:
                self.USER_INPUT = (self.payload.body.get("body"), None)
                self._check_if_trigger(self.USER_INPUT[0])

            case client.MessageTypeEnum.BUTTON | client.MessageTypeEnum.INTERACTIVE_BUTTON | \
                 client.MessageTypeEnum.INTERACTIVE_LIST:
                if "text" in self.payload.body:
                    self.USER_INPUT = (self.payload.body.get("text"), None)
                    self._check_if_trigger(self.USER_INPUT[0])
                else:
                    # for interactive button & list
                    self.USER_INPUT = (str(self.payload.body.get("id")), self.payload.body)
                    self._check_if_trigger(self.USER_INPUT[0])

            case client.MessageTypeEnum.LOCATION:
                self.USER_INPUT = (None, self.payload.body)

            case client.MessageTypeEnum.INTERACTIVE:
                self.USER_INPUT = (None, self.payload.body)

            case client.MessageTypeEnum.IMAGE | client.MessageTypeEnum.STICKER | \
                 client.MessageTypeEnum.DOCUMENT | client.MessageTypeEnum.AUDIO | client.MessageTypeEnum.VIDEO:
                self.USER_INPUT = (None, self.payload.body)

            case client.MessageTypeEnum.INTERACTIVE_FLOW:
                self.USER_INPUT = (self.payload.body.get("screen"), self.payload.body)

            case _:
                raise EngineResponseException(message="Unsupported response, kindly provide a valid response",
                                              data=self.CURRENT_STAGE)

    def _check_for_session_bypass(self) -> None:
        if TemplateConstants.SESSION in self.CURRENT_TEMPLATE:
            if bool(self.CURRENT_TEMPLATE.get(TemplateConstants.SESSION, False)) is True:
                self.IS_FROM_TRIGGER = False
                self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE,
                                  data=self.CURRENT_STAGE)

    def _check_save_checkpoint(self) -> None:
        if TemplateConstants.CHECKPOINT in self.CURRENT_TEMPLATE:
            self.session.save(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT,
                              data=self.CURRENT_STAGE)

    def _check_template_params(self, template: Dict = None) -> None:
        tpl = self.CURRENT_TEMPLATE if template is None else template

        self.HOOK_ARG.from_trigger = self.IS_FROM_TRIGGER

        if TemplateConstants.PARAMS in tpl:
            self.HOOK_ARG.params.update(tpl.get(TemplateConstants.PARAMS))

    async def _process_hook(self, stage_key: str) -> None:
        if stage_key in self.CURRENT_TEMPLATE:
            await HookService.process_hook(hook_dotted_path=self.CURRENT_TEMPLATE.get(stage_key), hook_arg=self.HOOK_ARG)

    async def _on_generate(self, next_template: Dict) -> None:
        if TemplateConstants.ON_GENERATE in next_template:
            await HookService.process_hook(hook_dotted_path=next_template.get(TemplateConstants.ON_GENERATE),
                                     hook_arg=self.HOOK_ARG)

    def _ack_user_message(self) -> None:
        # a fire & forget approach
        mark_as_read = self.config.read_receipts is True or TemplateConstants.READ_RECEIPT in self.CURRENT_TEMPLATE

        if mark_as_read is True:
            try:
                self.whatsapp.mark_as_read(self.user.msg_id)
            except:
                self.logger.warning("Failed to ack user message", stack_info=True)

    def _save_prop(self) -> None:
        # usually applicable to TEXT message types
        if TemplateConstants.PROP in self.CURRENT_TEMPLATE:
            self.session.save_prop(
                session_id=self.session_id,
                prop_key=self.CURRENT_TEMPLATE.get(TemplateConstants.PROP),
                data=self.USER_INPUT[0]
            )

    async def process_dynamic_route_hook(self) -> Union[str, None]:
        """
        Router hook is used to check next-route flow, instead of using template-level defined common, it
        reroutes / redirects / jumps to the response of the `router` hook.

        Router hook should return route stage inside the additional_data with key **EngineConstants.DYNAMIC_ROUTE_KEY**

        :return: str or None
        """

        if TemplateConstants.DYNAMIC_ROUTER in self.CURRENT_TEMPLATE:
            try:
                self._check_template_params()

                result = await HookService.process_hook(
                    hook_dotted_path=self.CURRENT_TEMPLATE.get(TemplateConstants.DYNAMIC_ROUTER),
                    hook_arg=self.HOOK_ARG)

                return result.additional_data.get(EngineConstants.DYNAMIC_ROUTE_KEY)

            except:
                self.logger.error("Failed to do dynamic route hook", stack_info=True)

        return None

    async def process_pre_hooks(self, next_stage_template: Dict = None) -> None:
        """
        Process all template hooks before message response is generated
        and send back to user

        :param next_stage_template: for processing next stage template else use current stage template
        :return: None
        """
        await HookService.process_global_hooks("pre", self.HOOK_ARG)

        self._check_template_params(next_stage_template)
        await self._on_generate(next_stage_template)

    async def process_post_hooks(self) -> None:
        """
        Process all hooks soon after receiving message from user.

        This processes the previous message which was processed & generated for sending
        to user

        ---

        e.g. Generate stage A template -> process all A's pre-hooks -> send to user.

        User responds to A message -> Engine processes A post-hooks.

        ---

        Return:
             None
        """
        await HookService.process_global_hooks("post", self.HOOK_ARG)

        self._ack_user_message()
        self._check_template_params()
        await self._process_hook(stage_key=TemplateConstants.VALIDATOR)
        await self._process_hook(stage_key=TemplateConstants.ON_RECEIVE)
        await self._process_hook(stage_key=TemplateConstants.MIDDLEWARE)
        self._save_prop()

    def setup(self) -> None:
        """
            Should be called before any other methods are called.

            Called after object instantiation.

            :return: None
        """
        self._get_current_template()
        self._get_message_body()
        self._check_for_session_bypass()
        self._check_save_checkpoint()

        self.HOOK_ARG = HookArg(
            session_id=self.session_id,
            session_manager=self.session,
            user=self.user,
            user_input=self.USER_INPUT[0],
            additional_data=self.USER_INPUT[1]
        )
