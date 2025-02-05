import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
        Engine configuration settings

        Best to use .env file, load envs and access them here
        for better security

        You can add more configurations here
    """

    # whatsapp config settings
    # see more under [WhatsAppConfig] class
    TOKEN = os.getenv("ACCESS_TOKEN")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    HUB_TOKEN = os.getenv("HUB_TOKEN")

    # engine settings
    # see more under [EngineConfig] class
    TEMPLATES_DIR = os.getenv("TEMPLATES_DIR")
    TRIGGERS_DIR = os.getenv("TRIGGERS_DIR")
    START_STAGE = os.getenv("START_STAGE")

    # for local emulator (if you know what you are doing)
    # requires knowledge and running of the emulator project
    # set this to False
    USE_EMULATOR = False
