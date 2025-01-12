from fastapi import Depends

import pywce
from example.engine_chatbot.settings import Settings
from pywce.engine_logger import get_engine_logger

logger = get_engine_logger(__name__)

# Global variable to hold the singleton instance
# ensure only 1 instance is available
_session_manager_instance: pywce.ISessionManager = None
_whatsapp_instance: pywce.WhatsApp = None
_engine_instance: pywce.PywceEngine = None


def get_session_manager():
    """
      You can pass your own ISessionManager implementation here
    :return: ISessionManager implementation
    """
    global _session_manager_instance
    if _session_manager_instance is None:
        logger.debug("Session manager not initialized, creating a new one")
        _session_manager_instance = pywce.DefaultSessionManager()

    return _session_manager_instance


def get_whatsapp_instance():
    global _whatsapp_instance

    if _whatsapp_instance is None:
        logger.debug("Whatsapp instance not initialized, creating a new one")
        wa_config = pywce.WhatsAppConfig(
            token=Settings.TOKEN,
            phone_number_id=Settings.PHONE_NUMBER_ID,
            hub_verification_token=Settings.HUB_TOKEN,
            use_emulator=Settings.USE_EMULATOR,
        )
        _whatsapp_instance = pywce.WhatsApp(whatsapp_config=wa_config)

    return _whatsapp_instance


def get_engine_instance(
        session_manager: pywce.ISessionManager = Depends(get_session_manager),
        whatsapp: pywce.WhatsApp = Depends(get_whatsapp_instance)
):
    global _engine_instance

    if _engine_instance is None:
        logger.debug("Engine instance not initialized, creating a new one")
        config = pywce.PywceEngineConfig(
            whatsapp=whatsapp,
            templates_dir=Settings.TEMPLATES_DIR,
            trigger_dir=Settings.TRIGGERS_DIR,
            start_template_stage=Settings.START_STAGE,
            session_manager=session_manager
        )

        _engine_instance = pywce.PywceEngine(config=config)

    return _engine_instance
