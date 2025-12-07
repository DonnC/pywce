from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable

from pydantic import BaseModel

from pywce.modules import client, storage, ISessionManager, DefaultSessionManager, history
from pywce.src.templates import EngineTemplate


@dataclass
class EngineConfig:
    """
        holds pywce engine configuration

        :var start_template_stage: The first templates to render when user initiates a chat
        :var session_manager: Implementation of ISessionManager
        :var handle_session_queue: if enabled, engine will internally track history of
                                     received messages to avoid duplicate message processing
        :var handle_session_inactivity: if enabled, engine will track user inactivity and
                                          reroutes user back to `start_template_stage` if inactive
        :var debounce_timeout_ms: reasonable time difference to process new message
        :var tag_on_reply: if enabled, engine will tag (reply) every message as it responds to it
        :var log_invalid_webhooks: if enabled, engine will log (WARN) all detailed invalid webhooks
        :var read_receipts: If enabled, engine will mark every message received as read.
    """
    whatsapp: client.WhatsApp
    start_template_stage: str
    report_template_stage: str
    storage_manager: storage.IStorageManager
    session_manager: ISessionManager
    handle_session_queue: bool = True
    handle_session_inactivity: bool = True
    tag_on_reply: bool = False
    read_receipts: bool = False
    log_invalid_webhooks: bool = False
    inactivity_timeout_min: int = 3
    debounce_timeout_ms: int = 3000
    webhook_timestamp_threshold_s: int = 10
    session_manager: ISessionManager = DefaultSessionManager()
    history_manager: Optional[history.IHistoryManager] = None
    on_hook_arg: Optional[Callable] = None
    external_renderer: Optional[Callable] = None
    global_pre_hooks: list[Callable] = field(default_factory=list)
    global_post_hooks: list[Callable] = field(default_factory=list)


@dataclass
class WorkerJob:
    engine_config: EngineConfig
    payload: client.ResponseStructure
    user: client.WaUser


class TemplateDynamicBody(BaseModel):
    """
        Model for flow & dynamic message types.

        Also used in `templates` hooks for dynamic message rendering

        :var dynamic_template: dynamic message model to render
        :var flow_payload: for flows that require initial data passed to a whatsapp flow or flow endpoint response
        :var render_template_payload: the templates dynamic variables to prefill
    """
    dynamic_template: Optional[EngineTemplate] = None
    flow_payload: Optional[Dict[Any, Any]] = None
    render_template_payload: Optional[Dict[str, Any]] = None


class HookArg(BaseModel):
    """
        Main hooks argument. All defined hooks must accept this arg in their functions and return the same arg.

        The model has all the data a hook might need to process any further business logic

        :var user: current whatsapp user object
        :var template_body: mainly returned from templates, dynamic or flow hooks
        :var additional_data: data from interactive & unprocessable message type responses. E.g a list, location, flow etc response
        :var flow: for flow message type, name of flow from the templates
        :var params: configured static templates params
        :var session_id: current session id
        :var user_input: the raw user input, usually a str if message was a button or text
        :var session_manager: session instance of the current user -> WaUser
        :var hook: the name / dotted path of the hook being executed
    """
    user: client.WaUser
    session_id: str
    user_input: Optional[Any] = None
    session_manager: Optional[ISessionManager] = None
    template_body: Optional[TemplateDynamicBody] = None
    from_trigger: bool = False
    flow: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    params: Dict[Any, Any] = field(default_factory=dict)
    hook: Optional[str] = None

    model_config = {
        "json_exclude": {"session_manager"},
        "arbitrary_types_allowed": True
    }

    def __str__(self):
        attrs = {
            "user": self.user,
            "session_id": self.session_id,
            "params": self.params,
            "template_body": self.template_body,
            "from_trigger": self.from_trigger,
            "user_input": self.user_input,
            "flow": self.flow,
            "hook": self.hook,
            "additional_data": self.additional_data
        }
        return f"HookArg({attrs})"


@dataclass
class WhatsAppServiceModel:
    config: EngineConfig
    template: EngineTemplate
    hook_arg: HookArg
    next_stage: Optional[str] = None


@dataclass
class QuickButtonModel:
    message: str
    buttons: List[str]
    title: str = None
    footer: str = None
    message_id: str = None
