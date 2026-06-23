import os

from pywce import Engine, EngineConfig, client, history

from example.common.recursive_storage import RecursiveYamlJsonStorageManager
from example.common.global_hooks import log_incoming_message


ROOT_DIR = os.path.dirname(__file__)
storage_manager = RecursiveYamlJsonStorageManager(ROOT_DIR)
history_manager = history.FileHistoryManager(base_dir=os.path.join(ROOT_DIR, "history"))

whatsapp = client.WhatsApp(
    client.WhatsAppConfig(
        token=os.getenv("ACCESS_TOKEN"),
        phone_number_id=os.getenv("PHONE_NUMBER_ID"),
        hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
        app_secret=os.getenv("APP_SECRET"),
        use_emulator=str(os.getenv("USE_EMULATOR", 0)) == "1",
    )
)

engine = Engine(
    EngineConfig(
        whatsapp=whatsapp,
        storage_manager=storage_manager,
        history_manager=history_manager,
        debounce_timeout_ms=0 if str(os.getenv("USE_EMULATOR", 0)) == "1" else 3000,
        start_template_stage="START-MENU",
        report_template_stage="REPORT",
        global_pre_hooks=[log_incoming_message],
    )
)
