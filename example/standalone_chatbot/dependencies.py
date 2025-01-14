import pywce
from example.standalone_chatbot.settings import Settings
from pywce.engine_logger import get_engine_logger

logger = get_engine_logger(__name__)

# Global variable to hold the singleton instance
# ensure only 1 instance is available
_whatsapp_instance: pywce.WhatsApp = None

def get_whatsapp_instance():
    global _whatsapp_instance

    if _whatsapp_instance is None:
        logger.debug("Whatsapp instance not initialized, creating a new one")
        wa_config = pywce.WhatsAppConfig(
            token=Settings.TOKEN,
            phone_number_id=Settings.PHONE_NUMBER_ID,
            hub_verification_token=Settings.HUB_TOKEN
        )
        _whatsapp_instance = pywce.WhatsApp(whatsapp_config=wa_config)

    return _whatsapp_instance
