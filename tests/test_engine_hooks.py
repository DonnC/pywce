import unittest

from pywce import DefaultSessionManager, Engine, EngineConfig, storage
from pywce.modules.whatsapp.model.message_type_enum import MessageTypeEnum
from pywce.src.constants import SessionConstants
from tests.engine_support import FakeWhatsApp, fixtures_dir, make_webhook_payload


class TestEngineHooks(unittest.TestCase):
    def setUp(self):
        self.whatsapp = FakeWhatsApp()
        self.session_manager = DefaultSessionManager()
        self.storage_manager = storage.YamlJsonStorageManager(
            str(fixtures_dir("engine_hooks", "templates")),
            str(fixtures_dir("engine_hooks", "triggers"))
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

    def test_on_receive_runs_before_on_generate_during_transition(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))
        self.engine.process_webhook(
            make_webhook_payload("hook", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        events = self.session_manager.get_global("events")
        self.assertEqual(["on_receive", "on_receive", "on_generate"], events)
        self.assertEqual(
            "HOOK-TARGET",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )

    def test_template_hook_renders_dynamic_message(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))
        self.engine.process_webhook(
            make_webhook_payload("dynamic", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_message", sent.method)
        self.assertEqual("Hello TDD", sent.payload["message"])


class TestEngineRouter(unittest.TestCase):
    def setUp(self):
        self.whatsapp = FakeWhatsApp()
        self.session_manager = DefaultSessionManager()
        self.storage_manager = storage.YamlJsonStorageManager(
            str(fixtures_dir("engine_router", "templates")),
            str(fixtures_dir("engine_router", "triggers"))
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

    def test_router_hook_redirects_next_stage(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))
        self.engine.process_webhook(
            make_webhook_payload("continue", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_message", sent.method)
        self.assertEqual("Report stage", sent.payload["message"])
        self.assertEqual(
            "REPORT",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )


if __name__ == "__main__":
    unittest.main()
