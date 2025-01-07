from dataclasses import dataclass
from typing import Dict

from modules.session import ISessionManager
from modules.session.impl.default_session_manager import DefaultSessionManager
from modules.whatsapp import ResponseStructure, WhatsApp


@dataclass
class PywceEngineConfig:
    """
        holds pywce engine configuration

        session_manager: Implementation of ISessionManager
    """
    whatsapp: WhatsApp
    templates_dir: str
    trigger_dir: str
    start_template_stage: str
    session_ttl: int = 30
    session_manager: ISessionManager = DefaultSessionManager()


@dataclass
class WorkerJob:
    engine_config: PywceEngineConfig
    payload: ResponseStructure
    templates: Dict
    triggers: Dict
