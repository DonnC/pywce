import unittest

from pywce import DefaultSessionManager, EngineConfig
from pywce.src.models import HookArg, WhatsAppServiceModel
from pywce.src.services.whatsapp_service import WhatsAppService
from pywce.src.templates import Template
from tests.engine_support import FakeWhatsApp
from pywce.modules.whatsapp.model.wa_user import WaUser


class TestWhatsAppServiceContract(unittest.TestCase):
    def setUp(self):
        self.whatsapp = FakeWhatsApp()
        self.session_manager = DefaultSessionManager()
        self.session = self.session_manager.session("263771234567")
        self.user = WaUser(
            name="Test User",
            wa_id="263771234567",
            msg_id="wamid-ctx",
            timestamp="1234567890"
        )
        self.config = EngineConfig(
            whatsapp=self.whatsapp,
            storage_manager=None,
            session_manager=self.session_manager,
            start_template_stage="START-MENU",
            report_template_stage="REPORT",
            debounce_timeout_ms=0,
        )

    def _send(self, template_dict: dict):
        template = Template.as_model(template_dict)
        model = WhatsAppServiceModel(
            config=self.config,
            template=template,
            next_stage="NEXT-STAGE",
            hook_arg=HookArg(
                user=self.user,
                session_id=self.user.wa_id,
                session_manager=self.session,
                user_input=None,
            )
        )
        service = WhatsAppService(model)
        return service.send_message()

    def test_text_template_uses_send_message(self):
        self._send({
            "kind": "text",
            "message": "Hello from pywce",
            "routes": {"re:.*": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_message", sent.method)
        self.assertEqual("Hello from pywce", sent.payload["message"])
        self.assertEqual("263771234567", sent.payload["recipient_id"])

    def test_button_template_uses_send_interactive(self):
        self._send({
            "kind": "button",
            "message": {
                "title": "Buttons",
                "body": "Pick one",
                "buttons": ["One", "Two"]
            },
            "routes": {"one": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        payload = sent.payload["payload"]
        self.assertEqual("button", payload["type"])
        self.assertEqual("Pick one", payload["body"]["text"])
        self.assertEqual("One", payload["action"]["buttons"][0]["reply"]["title"])

    def test_list_template_uses_send_interactive(self):
        self._send({
            "kind": "list",
            "message": {
                "title": "Drivers",
                "body": "Choose a driver",
                "button": "View",
                "sections": {
                    "Available": {
                        "1": {"title": "Donald", "description": "Honda Fit"},
                        "2": {"title": "Pamela", "description": "Toyota Aqua"}
                    }
                }
            },
            "routes": {"re:.*": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        payload = sent.payload["payload"]
        self.assertEqual("list", payload["type"])
        self.assertEqual("View", payload["action"]["button"])
        self.assertEqual("Donald", payload["action"]["sections"][0]["rows"][0]["title"])

    def test_media_template_uses_send_media(self):
        self._send({
            "kind": "media",
            "message": {
                "type": "image",
                "url": "https://example.com/image.png",
                "caption": "Preview"
            },
            "routes": {"re:.*": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_media", sent.method)
        self.assertEqual("https://example.com/image.png", sent.payload["media"])
        self.assertTrue(sent.payload["link"])
        self.assertEqual("Preview", sent.payload["caption"])

    def test_location_template_uses_send_location(self):
        self._send({
            "kind": "location",
            "message": {
                "lat": "-17.8252",
                "lon": "31.0335",
                "name": "Harare",
                "address": "Harare CBD"
            },
            "routes": {"re:.*": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_location", sent.method)
        self.assertEqual("-17.8252", sent.payload["lat"])
        self.assertEqual("31.0335", sent.payload["lon"])

    def test_request_location_template_uses_request_location(self):
        self._send({
            "kind": "request-location",
            "message": "Share your pickup point",
            "routes": {"re:.*": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("request_location", sent.method)
        self.assertEqual("Share your pickup point", sent.payload["message"])

    def test_flow_template_uses_send_interactive(self):
        self._send({
            "kind": "flow",
            "message": {
                "flow_id": "flow-123",
                "name": "BOOK_SCREEN",
                "title": "Start Booking",
                "body": "Tap below to continue",
                "button": "Begin"
            },
            "routes": {"re:.*": "START-MENU"}
        })

        sent = self.whatsapp.sent[-1]
        self.assertEqual("send_interactive", sent.method)
        payload = sent.payload["payload"]
        self.assertEqual("flow", payload["type"])
        self.assertEqual("flow-123", payload["action"]["parameters"]["flow_id"])
        self.assertEqual("Begin", payload["action"]["parameters"]["flow_cta"])


if __name__ == "__main__":
    unittest.main()
