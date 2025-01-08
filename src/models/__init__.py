from dataclasses import dataclass, field
from typing import Dict, Any

from modules.session import ISessionManager
from modules.session.impl.default_session_manager import DefaultSessionManager
from modules.whatsapp import ResponseStructure, WhatsApp, WaUser, MessageTypeEnum


@dataclass
class PywceEngineConfig:
    """
        holds pywce engine configuration

        session_manager: Implementation of ISessionManager

        session_ttl: In minutes
    """
    whatsapp: WhatsApp
    templates_dir: str
    trigger_dir: str
    start_template_stage: str
    handle_session_queue: bool = True
    handle_session_inactivity: bool = True
    session_ttl_min: int = 30
    inactivity_timeout_min: int = 3
    debounce_timeout_ms: int = 8000
    webhook_timestamp_threshold_s: int = 10
    session_manager: ISessionManager = DefaultSessionManager()


@dataclass
class WorkerJob:
    engine_config: PywceEngineConfig
    payload: ResponseStructure
    user: WaUser
    templates: Dict
    triggers: Dict


@dataclass
class TemplateDynamicBody:
    """
        type: specifies type of dynamic message body given
        initial_flow_payload: for flows that require initial data passed to a whatsapp flow
        render_template_payload: for `template` hooks and dynamic templates
    """
    typ: MessageTypeEnum = None
    initial_flow_payload: Dict[str, Any] = None
    render_template_payload: Dict[str, Any] = None


@dataclass
class HookArg:
    """
        additional_data: data from interactive message type responses. E.g a list / flow response
        flow: name of flow from the template
        params: configured template params
        user_input: the raw user input, usually a str if message was a button / text
    """
    user: WaUser
    params: Dict[str, Any] = field(default_factory=dict)
    template_body: TemplateDynamicBody = None
    from_trigger: bool = False
    user_input: str = None
    flow: str = None
    additional_data: Dict[str, Any] = None
    session_manager: ISessionManager = None
