import unittest

from modules.session.impl.default_session_manager import DefaultSessionManager
from modules.whatsapp import WhatsAppConfig, WhatsApp
from src.engine import PywceEngine
from src.models import PywceEngineConfig


class TestPywceEngine(unittest.TestCase):
    def setUp(self):
        session_manager = DefaultSessionManager()
        start_menu = "START-MENU"

        wa_config = WhatsAppConfig(
            token="TOKEN",
            phone_number_id="PHONE_NUMBER_ID",
            hub_verification_token="HUB_VERIFICATION_TOKEN",
            use_emulator=True
        )

        whatsapp_obj = WhatsApp(whatsapp_config=wa_config)

        config = PywceEngineConfig(
            whatsapp=whatsapp_obj,
            templates_dir="test_templates",
            trigger_dir="test_triggers",
            start_template_stage=start_menu,
            session_manager=session_manager
        )

        self.start_menu = start_menu
        self.engine = PywceEngine(config=config)

    def test_templates_loaded(self):
        self.assertIn(
            self.start_menu,
            self.engine.__TEMPLATES__,
            "Template not loaded properly. Configured start template menu is missing"
        )


if __name__ == '__main__':
    unittest.main()
