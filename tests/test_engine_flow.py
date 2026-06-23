import unittest

from pywce import DefaultSessionManager, Engine, EngineConfig, storage
from pywce.modules.whatsapp.model.message_type_enum import MessageTypeEnum
from pywce.src.constants import SessionConstants
from tests.engine_support import FakeWhatsApp, fixtures_dir, make_webhook_payload


class TestEngineFlow(unittest.TestCase):
    def setUp(self):
        self.whatsapp = FakeWhatsApp()
        self.session_manager = DefaultSessionManager()
        self.storage_manager = storage.YamlJsonStorageManager(
            str(fixtures_dir("templates")),
            str(fixtures_dir("triggers"))
        )
        self.engine = Engine(
            EngineConfig(
                whatsapp=self.whatsapp,
                storage_manager=self.storage_manager,
                session_manager=self.session_manager,
                start_template_stage="START-MENU",
                report_template_stage="REPORT",
                debounce_timeout_ms=0,
            )
        )
        self.session = self.session_manager.session("263771234567")

    def test_new_user_starts_at_configured_start_stage(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-start"))

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        self.assertEqual(
            "Test body",
            sent.payload["payload"]["body"]["text"]
        )
        self.assertEqual(
            "START-MENU",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )

    def test_button_selection_transitions_to_expected_next_stage(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))

        self.engine.process_webhook(
            make_webhook_payload("button1", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_message", sent.method)
        self.assertEqual("Test report", sent.payload["message"])
        self.assertEqual(
            "REPORT",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )
        self.assertEqual(
            "START-MENU",
            self.session.get("263771234567", SessionConstants.PREV_STAGE)
        )

    def test_menu_trigger_routes_back_to_start_stage(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))
        self.engine.process_webhook(
            make_webhook_payload("button1", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        self.engine.process_webhook(make_webhook_payload("Menu", msg_id="wamid-3"))

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        self.assertEqual(
            "Test body",
            sent.payload["payload"]["body"]["text"]
        )
        self.assertEqual(
            "START-MENU",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )

    def test_invalid_input_returns_recovery_message_without_changing_stage(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))

        self.engine.process_webhook(make_webhook_payload("not-a-route", msg_id="wamid-2"))

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        self.assertEqual(
            "Invalid response, please try again\n\nYou may click the buttons below to change options",
            sent.payload["payload"]["body"]["text"]
        )
        self.assertEqual(
            "START-MENU",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )


if __name__ == "__main__":
    unittest.main()

