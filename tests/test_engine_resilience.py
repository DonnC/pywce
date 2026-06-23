import unittest
from datetime import datetime, timedelta

from pywce import DefaultSessionManager, Engine, EngineConfig, storage
from pywce.modules.whatsapp.model.message_type_enum import MessageTypeEnum
from pywce.src.constants import SessionConstants
from tests.engine_support import FakeWhatsApp, fixtures_dir, make_webhook_payload


class TestEngineResilience(unittest.TestCase):
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
                inactivity_timeout_min=1,
            )
        )
        self.session = self.session_manager.session("263771234567")

    def test_duplicate_message_id_is_skipped(self):
        payload = make_webhook_payload("hello", msg_id="wamid-duplicate")

        self.engine.process_webhook(payload)
        first_count = len(self.whatsapp.sent)

        self.engine.process_webhook(payload)

        self.assertEqual(first_count, len(self.whatsapp.sent))

    def test_stale_webhook_is_skipped(self):
        old_ts = str((datetime.now() - timedelta(seconds=120)).timestamp())

        self.engine.process_webhook(
            make_webhook_payload("hello", msg_id="wamid-old", timestamp=old_ts)
        )

        self.assertEqual([], self.whatsapp.sent)

    def test_debounce_blocks_rapid_repeat_processing(self):
        self.engine = Engine(
            EngineConfig(
                whatsapp=self.whatsapp,
                storage_manager=self.storage_manager,
                session_manager=self.session_manager,
                start_template_stage="START-MENU",
                report_template_stage="REPORT",
                debounce_timeout_ms=60_000,
            )
        )

        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))
        first_count = len(self.whatsapp.sent)

        self.engine.process_webhook(
            make_webhook_payload("button1", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        self.assertEqual(first_count, len(self.whatsapp.sent))
        self.assertEqual(
            "START-MENU",
            self.session.get("263771234567", SessionConstants.CURRENT_STAGE)
        )

    def test_inactivity_resets_session_and_returns_expiry_message(self):
        self.engine.process_webhook(make_webhook_payload("hello", msg_id="wamid-1"))

        expired_at = (datetime.now() - timedelta(minutes=5)).isoformat()
        self.session.save("263771234567", SessionConstants.LAST_ACTIVITY_AT, expired_at)

        self.engine.process_webhook(
            make_webhook_payload("button1", msg_id="wamid-2", msg_type=MessageTypeEnum.BUTTON)
        )

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        self.assertEqual(
            "You have been inactive for a while. Let's start afresh",
            sent.payload["payload"]["body"]["text"]
        )
        self.assertEqual(
            {},
            self.session.fetch_all("263771234567", False)
        )


if __name__ == "__main__":
    unittest.main()
