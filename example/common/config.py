import os
from typing import Optional

from dotenv import load_dotenv

from pywce import Engine, storage, EngineConfig, client
from .global_hooks import log_incoming_message

load_dotenv()

private_key: Optional[str] = None

if os.getenv('PRIVATE_KEY_PATH') is not None:
    with open(os.getenv('PRIVATE_KEY_PATH'), 'r') as key_file:
        private_key = key_file.read()

# create a .env and set the appropriate keys
_wa_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
    app_secret=os.getenv("APP_SECRET"),
    private_key=private_key,
    private_key_pwd=os.getenv("PRIVATE_KEY_PASS_KEY")
)

whatsapp = client.WhatsApp(whatsapp_config=_wa_config)

hybrid_storage = storage.YamlJsonStorageManager(os.getenv("TEMPLATES_DIR"), os.getenv("TRIGGERS_DIR"))

_eng_config = EngineConfig(
    whatsapp=whatsapp,
    storage_manager=hybrid_storage,
    start_template_stage=os.getenv("START_STAGE"),

    # optional fields, depends on the example project being run
    global_pre_hooks=[log_incoming_message]
)

engine = Engine(config=_eng_config)
