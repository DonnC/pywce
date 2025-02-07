import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
        Save your settings in a secure .env file
    """
    # see more under [WhatsAppConfig] class
    TOKEN = os.getenv("ACCESS_TOKEN")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    HUB_TOKEN = os.getenv("WEBHOOK_HUB_TOKEN")
