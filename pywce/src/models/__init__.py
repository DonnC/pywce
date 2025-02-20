from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from pywce.modules import *
from pywce.modules import client
from pywce.src.constants import TemplateTypeConstants


@dataclass
class EngineConfig:
    """
        holds pywce engine configuration

        :var templates_dir: Directory path where (templates) YAML files are located
        :var start_template_stage: The first template to render when user initiates a chat
        :var session_manager: Implementation of ISessionManager
        :var handle_session_queue: if enabled, engine will internally track history of
                                     received messages to avoid duplicate message processing
        :var handle_session_inactivity: if enabled, engine will track user inactivity and
                                          reroutes user back to `start_template_stage` if inactive
        :var debounce_timeout_ms: reasonable time difference to process new message
        :var tag_on_reply: if enabled, engine will tag (reply) every message as it responds to it
        :var log_invalid_webhooks: if enabled, engine will log (WARN) all detailed invalid webhooks
        :var read_receipts: If enabled, engine will mark every message received as read.
        :var ext_handler_hook: path to external chat handler hook. If message is received and ext_handler is active,
                                call this hook to handle requests
    """
    whatsapp: client.WhatsApp
    templates_dir: str
    trigger_dir: str
    start_template_stage: str
    ext_handler_hook: str = None
    handle_session_queue: bool = True
    handle_session_inactivity: bool = True
    tag_on_reply: bool = False
    read_receipts: bool = False
    log_invalid_webhooks: bool = False
    session_ttl_min: int = 30
    inactivity_timeout_min: int = 3
    debounce_timeout_ms: int = 6000
    webhook_timestamp_threshold_s: int = 10
    session_manager: ISessionManager = DefaultSessionManager()


@dataclass
class WorkerJob:
    engine_config: EngineConfig
    payload: client.ResponseStructure
    user: client.WaUser
    templates: Dict
    triggers: Dict
    session_manager: ISessionManager


@dataclass
class TemplateDynamicBody:
    """
        Model for flow & dynamic message types.

        Also used in `template` hooks for dynamic message rendering

        :var typ: specifies type of dynamic message body to create
        :var initial_flow_payload: for flows that require initial data passed to a whatsapp flow
        :var render_template_payload: `for dynamic templates` -> the dynamic message template body
                                        `for template templates` -> the template dynamic variables to prefill
    """
    typ: TemplateTypeConstants = None
    initial_flow_payload: Dict[str, Any] = None
    render_template_payload: Dict[str, Any] = None


@dataclass
class HookArg:
    """
        Main hooks argument. All defined hooks must accept this arg in their functions and return the same arg.

        The model has all the data a hook might need to process any further business logic

        :var user: current whatsapp user object
        :var template_body: mainly returned from template, dynamic or flow hooks
        :var additional_data: data from interactive & unprocessable message type responses. E.g a list, location, flow etc response
        :var flow: for flow message type, name of flow from the template
        :var params: configured static template params
        :var session_id: current session id
        :var user_input: the raw user input, usually a str if message was a button or text
        :var session_manager: session instance of the current user -> WaUser
    """
    user: client.WaUser
    params: Dict[str, Any] = field(default_factory=dict)
    template_body: TemplateDynamicBody = None
    from_trigger: bool = False
    user_input: str = None
    flow: str = None
    additional_data: Dict[str, Any] = None
    session_id: str = None
    session_manager: ISessionManager = None

    def __str__(self):
        attrs = {
            "user": self.user,
            "session_id": self.session_id,
            "params": self.params,
            "template_body": self.template_body,
            "from_trigger": self.from_trigger,
            "user_input": self.user_input,
            "flow": self.flow,
            "additional_data": self.additional_data
        }
        return f"HookArg({attrs})"


@dataclass
class WhatsAppServiceModel:
    template_type: TemplateTypeConstants
    template: Dict
    whatsapp: client.WhatsApp
    user: client.WaUser
    hook_arg: HookArg = None
    next_stage: str = None
    handle_session_activity: bool = False
    tag_on_reply: bool = False
    read_receipts: bool = False


@dataclass
class QuickButtonModel:
    message: str
    buttons: List[str]
    title: str = None
    footer: str = None
    message_id: str = None


@dataclass
class ExternalHandlerResponse:
    """
    Model for external chat handler

    Example use case:
        1. Live Support
        2. AI Agent


    :var typ (TemplateTypeConstants): type of the chat template to render to user
    :var recipient_id (str): whatsapp user wa id to respond to
    :var message (str): the message body to render to user
    :var options (list): if typ is button / list - the list of options to render
    :var reply_message_id (str): which message to reply to
    """
    typ: TemplateTypeConstants
    recipient_id: str
    message: str
    options: List
    reply_message_id: Optional[str]
