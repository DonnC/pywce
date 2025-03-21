"""
pywce: Python WhatsApp Chatbot Engine

pywce is a package for creating WhatsApp chatbots using a template-driven approach. It decouples
the engine from the WhatsApp client library, allowing developers to use them independently or
together. Templates use YAML to define conversation flows, making chatbot development simpler
and more intuitive.

Modules:
- session: Manage session states for the engine.
- whatsapp: Interact with WhatsApp Cloud API.
- engine: Core logic for template-driven chatbot interactions.

Author: Donald Chinhuru

TODO: AI agents
    : Save conversation history to file
    : Create a function to create agent prompt with pre-appended prompt
    : Handle agent response and process supported message types.
"""

from pywce.modules import client, DefaultSessionManager, storage
from pywce.modules.session import ISessionManager
from pywce.modules.storage import IStorageManager
from pywce.src.constants import SessionConstants, EngineConstants, TemplateTypeConstants
from pywce.src.engine import Engine
from pywce.src.models import HookArg, TemplateDynamicBody, EngineConfig, ExternalHandlerResponse
from pywce.src.services import HookService, hook
import pywce.src.services.ai_service as ai
from pywce.src.utils import pywce_logger

__author__ = "Donald Chinhuru"
__email__ = "donychinhuru@gmail.com"
__license__ = "MIT"
__name__ = "pywce"
__all__ = [
    # modules
    "client",
    "ISessionManager",
    "DefaultSessionManager",
    "storage",

    # engine
    "Engine",
    "EngineConfig",
    "ExternalHandlerResponse",

    # ai
    "ai",

    # hook
    "HookArg",
    "TemplateDynamicBody",
    "HookService",
    "hook",

    # util
    "pywce_logger",

    # constants
    "SessionConstants",
    "EngineConstants",
    "TemplateTypeConstants"
]
__doc__ = (
    "A batteries-included WhatsApp ChatBot builder framework library using a template-driven approach. "
    "Supports YAML templates and provides a modular structure for integrating "
    "with WhatsApp Cloud API."
)
