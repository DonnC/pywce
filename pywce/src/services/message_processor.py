from typing import Dict, Tuple, Any, Union

from pywce.engine_logger import get_engine_logger
from pywce.modules.session import ISessionManager
from pywce.modules.whatsapp import MessageTypeEnum
from pywce.src.constants.engine import EngineConstants
from pywce.src.constants.session import SessionConstants
from pywce.src.constants.template import TemplateConstants
from pywce.src.exceptions import EngineInternalException, EngineResponseException
from pywce.src.models import WorkerJob, HookArg
from pywce.src.services.hook_service import HookService
from pywce.src.utils.engine_util import EngineUtil


class MessageProcessor:
    """
        Main message processor class

        Processes current message against template
        Processes all template hooks
    """

    CURRENT_TEMPLATE: Dict
    IS_FIRST_TIME: bool = False
    IS_FROM_TRIGGER: bool = False
    CURRENT_STAGE: str
    HOOK_ARG: HookArg

    # (input: str, data: dict)
    USER_INPUT: Tuple[Any, Any]

    def __init__(self, data: WorkerJob):
        self.data = data
        self.user = data.user
        self.config = data.engine_config
        self.whatsapp = data.engine_config.whatsapp
        self.payload = data.payload

        self.session_id = self.user.wa_id
        self.session: ISessionManager = self.config.session_manager.session(session_id=self.user.wa_id)

        self.logger = get_engine_logger(__name__)

    def __is_stage_in_repository__(self, template_stage: str):
        return template_stage in self.data.templates

    def __get_stage_template__(self, template_stage_name: str) -> Dict:
        tpl = self.data.templates.get(template_stage_name)
        if tpl is None:
            raise EngineInternalException(message=f"Template {template_stage_name} not found")
        return tpl

    def __get_current_template__(self) -> None:
        current_stage_in_session = self.session.get(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE)

        if current_stage_in_session is None:
            self.CURRENT_STAGE = self.config.start_template_stage

            # assume user is new or session cleared
            if self.__is_stage_in_repository__(self.CURRENT_STAGE) is False:
                raise EngineInternalException(message="Configured start stage does not exist",
                                              data=self.CURRENT_STAGE)

            self.CURRENT_TEMPLATE = self.__get_stage_template__(self.CURRENT_STAGE)
            self.IS_FIRST_TIME = True

            self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE, data=self.CURRENT_STAGE)
            self.session.save(session_id=self.session_id, key=SessionConstants.PREV_STAGE, data=self.CURRENT_STAGE)
            return

        if self.__is_stage_in_repository__(current_stage_in_session) is False:
            raise EngineInternalException(message="Template stage not found in template context map",
                                          data=current_stage_in_session)

        self.CURRENT_STAGE = current_stage_in_session
        self.CURRENT_TEMPLATE = self.__get_stage_template__(current_stage_in_session)

    def __check_if_trigger__(self, possible_trigger_input: str = None) -> None:
        if possible_trigger_input is None:
            return

        for _stage, _pattern in self.data.triggers.items():
            if EngineUtil.is_regex_input(_pattern):
                if EngineUtil.is_regex_pattern_match(EngineUtil.extract_pattern(_pattern), possible_trigger_input):
                    if self.__is_stage_in_repository__(_stage) is False:
                        raise EngineInternalException(
                            message="Template stage not found in template context map",
                            data=_stage
                        )

                    self.CURRENT_TEMPLATE = self.__get_stage_template__(_stage)
                    self.CURRENT_STAGE = _stage
                    self.IS_FROM_TRIGGER = True
                    self.logger.warning("Template change from trigger. Stage: " + _stage)
                    return

        # TODO: check if current msg id is null, throw Ambiguous old webhook exc

    def __get_message_body__(self) -> None:
        """
        for type that cannot be processed easily e.g.
        MEDIA, LOCATION_REQUEST & FLOW, the raw response data will be available under
        USER_INPUT[1] &
        HookArg.additional_data
        but HookArg.user_input will be None

        else, the user selection or input will be available under
        USER_INPUT[0]
        HookArg.user_input

        If the resulting USER_INPUT[0] is None -> it signifies that user message cannot be processed e.g. Image
        In that case, bot hook should process it further on what to do with it
        The template should just define next stage to go to in the template routes e.g
        {"re:.*": "NEXT-STAGE"}

        :return: None
        """

        match self.payload.model:
            case MessageTypeEnum.TEXT:
                self.USER_INPUT = (self.payload.body.get("body"), None)
                self.__check_if_trigger__(self.USER_INPUT[0])

            case MessageTypeEnum.BUTTON | MessageTypeEnum.INTERACTIVE_BUTTON | MessageTypeEnum.INTERACTIVE_LIST:
                if "text" in self.payload.body:
                    self.USER_INPUT = (self.payload.body.get("text"), None)
                    self.__check_if_trigger__(self.USER_INPUT[0])
                else:
                    # for interactive button & list
                    self.USER_INPUT = (str(self.payload.body.get("id")), self.payload.body)
                    self.__check_if_trigger__(self.USER_INPUT[0])

            case MessageTypeEnum.LOCATION:
                self.USER_INPUT = (None, self.payload.body)

            case MessageTypeEnum.INTERACTIVE:
                self.USER_INPUT = (None, self.payload.body)

            case MessageTypeEnum.IMAGE | MessageTypeEnum.STICKER | MessageTypeEnum.DOCUMENT | MessageTypeEnum.AUDIO | MessageTypeEnum.VIDEO:
                self.USER_INPUT = (None, self.payload.body)

            case MessageTypeEnum.INTERACTIVE_FLOW:
                self.USER_INPUT = (None, self.payload.body)

            case _:
                raise EngineResponseException(message="Unsupported response, kindly provide a valid response",
                                              data=self.CURRENT_STAGE)

    def __check_for_session_bypass__(self) -> None:
        if TemplateConstants.SESSION in self.CURRENT_TEMPLATE:
            if bool(self.CURRENT_TEMPLATE.get(TemplateConstants.SESSION, False)) is True:
                self.IS_FROM_TRIGGER = False
                self.session.save(session_id=self.session_id, key=SessionConstants.CURRENT_STAGE,
                                  data=self.CURRENT_STAGE)

    def __check_save_checkpoint__(self) -> None:
        if TemplateConstants.CHECKPOINT in self.CURRENT_TEMPLATE:
            self.session.save(session_id=self.session_id, key=SessionConstants.LATEST_CHECKPOINT,
                              data=self.CURRENT_STAGE)

    def __check_template_params__(self, template: Dict = None) -> None:
        tpl = self.CURRENT_TEMPLATE if template is None else template

        self.HOOK_ARG.from_trigger = self.IS_FROM_TRIGGER

        if TemplateConstants.PARAMS in tpl:
            self.HOOK_ARG.params.update(tpl.get(TemplateConstants.PARAMS))

    def __process_hook__(self, stage_key: str) -> None:
        if stage_key in self.CURRENT_TEMPLATE:
            HookService.process_hook(hook_dotted_path=self.CURRENT_TEMPLATE.get(stage_key), hook_arg=self.HOOK_ARG)

    # - start template hooks processing -
    def __on_generate__(self, next_template: Dict) -> None:
        if TemplateConstants.ON_GENERATE in next_template:
            HookService.process_hook(hook_dotted_path=next_template.get(TemplateConstants.ON_GENERATE),
                                     hook_arg=self.HOOK_ARG)

    def __bluetick_message__(self) -> None:
        # a fire & forget approach
        if TemplateConstants.READ_RECEIPT in self.CURRENT_TEMPLATE:
            try:
                self.whatsapp.mark_as_read(self.user.msg_id)
            except:
                self.logger.warning("Failed to do read receipts (blue-tick) message")

    def __save_prop__(self) -> None:
        # usually applicable to TEXT message types
        if TemplateConstants.PROP in self.CURRENT_TEMPLATE:
            self.session.save_prop(
                session_id=self.session_id,
                prop_key=self.CURRENT_TEMPLATE.get(TemplateConstants.PROP),
                data=self.USER_INPUT[0]
            )

    def process_dynamic_route_hook(self) -> Union[str, None]:
        """
        Check if current template has a `router` hook specified

        Router hook is used to check next-route flow, instead of using routes defined, it
        reroutes to the response of the `router` hook.

        Router hook should return route stage inside the additional_data with key [EngineConstants.DYNAMIC_ROUTE_KEY]

        :return: str or None
        """

        if TemplateConstants.DYNAMIC_ROUTER in self.CURRENT_TEMPLATE:
            try:
                self.__check_template_params__()

                result = HookService.process_hook(
                    hook_dotted_path=self.CURRENT_TEMPLATE.get(TemplateConstants.DYNAMIC_ROUTER),
                    hook_arg=self.HOOK_ARG)

                return result.additional_data.get(EngineConstants.DYNAMIC_ROUTE_KEY)

            except Exception as e:
                self.logger.error("Failed to do dynamic route hook", exc_info=True)

        return None

    def process_pre_hooks(self, next_stage_template: Dict = None) -> None:
        """
        Process all hooks before message response is generated
        and send back to user

        :param next_stage_template: for processing next stage template else use current stage template
        :return: None
        """
        self.__check_template_params__(next_stage_template)
        self.__on_generate__(next_stage_template)

    def process_post_hooks(self) -> None:
        """
        Process all hooks soon after receiving message from user.

        This processes the previous message which was processed & generated for sending
        to user

        e.g. Generate stage A template, process all A's pre-hooks and send to user.
        User respond message of stage A. Engine processes all post-hooks of stage A template
        before processing any next stage template.

        :return: None
        """
        self.__bluetick_message__()
        self.__check_template_params__()
        self.__process_hook__(stage_key=TemplateConstants.VALIDATOR)
        self.__process_hook__(stage_key=TemplateConstants.ON_RECEIVE)
        self.__process_hook__(stage_key=TemplateConstants.MIDDLEWARE)
        self.__save_prop__()

        # - end template hooks -

    def setup(self) -> None:
        """
            Should be called before any other methods are called.

            Called after object instantiation.

            :return: None
            """
        self.__get_current_template__()
        self.__get_message_body__()
        self.__check_for_session_bypass__()
        self.__check_save_checkpoint__()

        self.HOOK_ARG = HookArg(
            session_manager=self.session,
            user=self.user,
            user_input=self.USER_INPUT[0],
            additional_data=self.USER_INPUT[1]
        )
