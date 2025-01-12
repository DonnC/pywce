class Settings:
    """
        Engine configuration settings

        Best to use .env file, load envs and access them here
        for better security

        You can add more configurations here
    """

    # whatsapp config settings
    # see more under [WhatsAppConfig] class
    TOKEN = "account-access-token"
    PHONE_NUMBER_ID = "account-phone-number-id"
    HUB_TOKEN = "your-hub-verification-token"

    # engine settings
    # see more under [PywceEngineConfig] class
    TEMPLATES_DIR = "templates"
    TRIGGERS_DIR = "triggers"
    START_STAGE = "EM-START-MENU"  # START-MENU

    # for local emulator (if you know what you are doing)
    # requires knowledge and running of the emulator project
    # set this to False
    USE_EMULATOR = True
