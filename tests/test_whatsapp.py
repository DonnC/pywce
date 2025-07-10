import unittest
from unittest.mock import patch, MagicMock

from pywce.modules.whatsapp import WhatsApp
from pywce.modules.whatsapp.config import WhatsAppConfig
from pywce.modules.whatsapp.model.message_type_enum import MessageTypeEnum


class TestWhatsApp(unittest.TestCase):
    def setUp(self):
        self.config = WhatsAppConfig(
            token="test_token",
            phone_number_id="test_phone_number_id",
            hub_verification_token="test_hub_verification_token"
        )
        self.mock_listener = MagicMock()
        self.whatsapp = WhatsApp(self.config, on_send_listener=self.mock_listener)
        self.expected_response = {"success": True}

    def setup_mock_client(self, mock_client):
        """Helper method to setup common mock behavior"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.expected_response
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        return mock_response

    @patch("pywce.modules.whatsapp.Client")
    def test_send_message(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.send_message(
            recipient_id="1234567890", 
            message="Hello world"
        )
        self.assertEqual(self.expected_response, result)

    @patch("pywce.modules.whatsapp.Client")
    def test_send_reaction(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.send_reaction(
            recipient_id="1234567890", 
            emoji="😂", 
            message_id="msg123"
        )
        self.assertEqual(self.expected_response, result)

    @patch("pywce.modules.whatsapp.Client")
    def test_send_template(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.send_template(
            recipient_id="1234567890",
            template="template_name",
            components=[{"type": "body", "parameters": [{"type": "text", "text": "Test"}]}]
        )
        self.assertEqual(self.expected_response, result)

    @patch("pywce.modules.whatsapp.Client")
    def test_send_location(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.send_location(
            recipient_id="1234567890",
            lat="12.9716",
            lon="77.5946",
            name="Test Location",
            address="Test Address"
        )
        self.assertEqual(self.expected_response, result)

    @patch("pywce.modules.whatsapp.Client")
    def test_send_media(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.send_media(
            recipient_id="1234567890",
            media="media_id",
            media_type=MessageTypeEnum.IMAGE,
            caption="Test Caption"
        )
        self.assertEqual(self.expected_response, result)

    @patch("pywce.modules.whatsapp.Client")
    def test_mark_as_read(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.mark_as_read(message_id="msg123")
        self.assertEqual(self.expected_response, result)

    @patch("pywce.modules.whatsapp.Client")
    def test_show_typing_indicator(self, mock_client):
        self.setup_mock_client(mock_client)
        result = self.whatsapp.show_typing_indicator(message_id="msg123")
        self.assertEqual(self.expected_response, result)


if __name__ == "__main__":
    unittest.main()