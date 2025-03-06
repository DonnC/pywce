import os

from dotenv import load_dotenv

from pywce import Engine, client, EngineConfig
from .global_hooks import log_incoming_message

load_dotenv()

# create a .env and set the appropriate keys
_wa_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
    app_secret=os.getenv("APP_SECRET"),
    use_emulator=int(os.getenv("USE_EMULATOR", 0)) == 1
)

whatsapp = client.WhatsApp(_wa_config)

_eng_config = EngineConfig(
    whatsapp=whatsapp,
    templates_dir=os.getenv("TEMPLATES_DIR"),
    trigger_dir=os.getenv("TRIGGERS_DIR"),
    start_template_stage=os.getenv("START_STAGE"),

    # optional fields, depends on the example project being run
    global_pre_hooks=[log_incoming_message],
    ext_handler_hook="example.ai_agents.hooks.ai_hook.agent_processor"
)

engine = Engine(config=_eng_config)
