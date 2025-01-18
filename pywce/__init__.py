"""
pywce: Python WhatsApp Cloud Engine

pywce is a package for creating WhatsApp chatbots using a template-driven approach. It decouples
the engine from the WhatsApp client library, allowing developers to use them independently or
together. Templates use YAML to define conversation flows, making chatbot development simpler
and more intuitive.

Modules:
- session: Manage session states for the engine.
- whatsapp: Interact with WhatsApp Cloud API.
- engine: Core logic for template-driven chatbot interactions.

Author: Donald Chinhuru
"""

from pywce.src.models import *
from pywce.modules.session import ISessionManager
from pywce.modules.session.dict_session_manager import DictSessionManager
from pywce.modules.whatsapp import WhatsApp, WhatsAppConfig
from pywce.src.engine import PywceEngine, PywceEngineConfig
from pywce.src.services.hook_service import HookService, hook

__author__ = "Donald Chinhuru"
__email__ = "donychinhuru@gmail.com"
__license__ = "MIT"
__name__ = "pywce"
__all__ = [
    "ISessionManager",
    "DictSessionManager",
    "WaUser",
    "WhatsApp",
    "WhatsAppConfig",
    "PywceEngine",
    "PywceEngineConfig",
    "HookArg",
    "TemplateDynamicBody",
    "HookService",
    "MessageTypeEnum",
    "hook",
]
__doc__ = (
    "A Python package for creating chatbots using a template-driven approach. "
    "Supports YAML templates and provides a modular structure for integrating "
    "with WhatsApp Cloud API."
)
