import os

from dotenv import load_dotenv

from pywce import Engine, client, storage, EngineConfig
from .global_hooks import log_incoming_message

load_dotenv()

hybrid_storage = storage.YamlJsonStorageManager(os.getenv("TEMPLATES_DIR"), os.getenv("TRIGGERS_DIR"))

# create a .env and set the appropriate keys
_wa_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
    app_secret=os.getenv("APP_SECRET")
)

whatsapp = client.WhatsApp(_wa_config)

_eng_config = EngineConfig(
    whatsapp=whatsapp,
    storage_manager=hybrid_storage,
    start_template_stage=os.getenv("START_STAGE"),

    # optional fields, depends on the example project being run
    global_pre_hooks=[log_incoming_message]
)

engine = Engine(config=_eng_config)
