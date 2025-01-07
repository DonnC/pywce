from dataclasses import dataclass
from typing import Dict

from modules.session import ISessionManager
from modules.session.impl.default_session_manager import DefaultSessionManager
from modules.whatsapp import ResponseStructure, WhatsApp, WaUser


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
    handle_session_inactivity:bool = True
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
