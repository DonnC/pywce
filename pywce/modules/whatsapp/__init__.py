"""
Originally cloned from https://github.com/Neurotech-HQ/heyoo PR by
https://github.com/oca159/heyoo/tree/main

Unofficial python wrapper for the WhatsApp Cloud API.
"""

import mimetypes
import os
from typing import Dict, Any, List, Union

from httpx import AsyncClient

from pywce.engine_logger import get_engine_logger
from pywce.modules.whatsapp.config import WhatsAppConfig
from pywce.modules.whatsapp.message_utils import MessageUtils
from pywce.modules.whatsapp.model import *

_logger = get_engine_logger(__name__)


class WhatsApp:
    """
    WhatsApp Object
    """

    def __init__(self, whatsapp_config: WhatsAppConfig):
        """
        Initialize the WhatsApp Object

        Args:
            config[WhatsAppConfig]: config object
        """
        self.config = whatsapp_config
        self.base_url = f"https://graph.facebook.com/{self.config.version}"
        self.url = f"{self.base_url}/{self.config.phone_number_id}/messages"

        if self.config.use_emulator is True:
            self.url = self.config.emulator_url

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.token}"
        }
        self.util = self.Utils(self)

    async def _send_request(self, message_type: str, recipient_id: str, data: Dict[str, Any]):
        """
        Send a request to the official WhatsApp API

        :param message_type:
        :param recipient_id:
        :param data:
        :return:
        """

        _logger.debug(f"Sending {message_type} to {recipient_id}")

        async with AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, json=data)

        if response.status_code == 200:
            return response.json()

        else:
            _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
            return response.json()

    async def send_message(self, recipient_id: str, message: str, recipient_type: str = "individual",
                           message_id: str = None, preview_url: bool = True):
        """
         Sends a text message to a WhatsApp user

         Args:
                message[str]: Message to be sent to the user
                recipient_id[str]: Phone number of the user with country code without +
                recipient_type[str]: Type of the recipient, either individual or group
                preview_url[bool]: Whether to send a preview url or not
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "text",
            "text": {"preview_url": preview_url, "body": message},
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type='Message', recipient_id=recipient_id, data=data)

    async def send_reaction(self, recipient_id: str, emoji: str, message_id: str, recipient_type: str = "individual"):
        """
        Sends a reaction message to a WhatsApp user's message asynchronously.

        Args:
            emoji (str): Emoji to become a reaction to a message. Ex.: '\uD83D\uDE00' (😀)
            message_id (str): Message id for a reaction to be attached to
            recipient_id (str): Phone number of the user with country code without +
            recipient_type (str): Type of the recipient, either individual or group
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "reaction",
            "reaction": {"message_id": message_id, "emoji": emoji},
        }

        return await self._send_request(message_type='Reaction', recipient_id=recipient_id, data=data)

    async def send_template(self, recipient_id: str, template: str, components: List[Dict], message_id: str = None,
                            lang: str = "en_US"):
        """
        Asynchronously sends a template message to a WhatsApp user. Templates can be:
            1. Text template
            2. Media based template
            3. Interactive template
        You can customize the template message by passing a dictionary of components.
        Find available components in the documentation:
        https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates

        Args:
            template (str): Template name to be sent to the user.
            recipient_id (str): Phone number of the user with country code without +.
            message_id: if replying to a message, include the previous message id here
            components (list): List of components to be sent to the user.
            lang (str): Language of the template message, default is "en_US".
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": lang},
                "components": components,
            },
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type='Template', recipient_id=recipient_id, data=data)

    async def send_location(self, recipient_id: str, lat: str, lon: str, name: str = None, address: str = None,
                            message_id: str = None):
        """
        Asynchronously sends a location message to a WhatsApp user.

        Args:
            lat (str): Latitude of the location.
            lon (str): Longitude of the location.
            name (str): Name of the location.
            address (str): Address of the location.
            recipient_id (str): Phone number of the user with country code without +.
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "location",
            "location": {
                "latitude": lat,
                "longitude": lon,
                "name": name,
                "address": address,
            },
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type='Location', recipient_id=recipient_id, data=data)

    async def request_location(self, recipient_id: str, message: str, message_id: str = None):
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "recipient_type": "individual",
            "type": "interactive",
            "interactive": {
                "type": "location_request_message",
                "body": {
                    "text": message
                },
                "action": {
                    "name": "send_location"
                }
            }
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type='RequestLocation', recipient_id=recipient_id, data=data)

    async def send_media(
            self,
            recipient_id: str,
            media: str,
            media_type: MessageTypeEnum,
            recipient_type="individual",
            link: bool = False,
            caption: str = None,
            filename: str = None,
            message_id: str = None
    ):
        """
        Asynchronously send media message to a WhatsApp user.

        There are two ways to send media message to a user, either by passing the media id or by passing the media link.
        Media id is the id of the media uploaded to the cloud API.

        Args:
            media (str): media id or link of the sticker.
            recipient_id (str): Phone number of the user with country code without +.
            recipient_type (str): Type of the recipient, either individual or group.
            link (bool): Whether to send a sticker id or a sticker link, True means that the sticker is an id, False means the sticker is a link.
        """

        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": media_type.name.lower()
        }

        match media_type:
            case MessageTypeEnum.STICKER:
                data["recipient_type"] = recipient_type
                data[media_type.name.lower()] = {"link": media} if link else {"id": media}

            case MessageTypeEnum.AUDIO:
                data[media_type.name.lower()] = {"link": media} if link else {"id": media}

            case MessageTypeEnum.VIDEO:
                data[media_type.name.lower()] = {"link": media, "caption": caption} if link \
                    else {"id": media, "caption": caption}

            case MessageTypeEnum.DOCUMENT:
                data[media_type.name.lower()] = {"link": media, "caption": caption, "filename": filename} if link \
                    else {"id": media, "caption": caption}

            case MessageTypeEnum.IMAGE:
                data["recipient_type"] = recipient_type
                data[MessageTypeEnum.IMAGE.name.lower()] = {"link": media, "caption": caption} if link \
                    else {"id": media, "caption": caption}

            case _:
                raise TypeError(f"Unknown media message type {media_type.name}")

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type=media_type.name.title(), recipient_id=recipient_id, data=data)

    async def send_contacts(self, recipient_id: str, contacts: List[Dict[Any, Any]], message_id: str = None):
        """
        Asynchronously sends a list of contacts to a WhatsApp user.

        Args:
            contacts: List of contacts to send, structured according to the WhatsApp API requirements.
            recipient_id: Phone number of the user with country code without +.

        REFERENCE:
        https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#contacts-object
        """

        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "contacts",
            "contacts": contacts,
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type='Contacts', recipient_id=recipient_id, data=data)

    async def mark_as_read(self, message_id: str) -> Dict[Any, Any]:
        """
        Asynchronously marks a message as read using the WhatsApp Cloud API.

        Args:
            message_id (str): ID of the message to be marked as read.

        Returns:
            Dict[Any, Any]: Response from the API.
        """
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        return await self._send_request(message_type='MarkAsRead', recipient_id=message_id, data=data)

    async def send_interactive(self, recipient_id: str, payload: Dict[Any, Any], message_id: str = None):
        """
        Asynchronously sends an interactive message to a WhatsApp user.

        Args:
            payload (dict): A dictionary containing the interactive type payload.
            recipient_id (str): Phone number of the user with country code without +.
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": payload
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self._send_request(message_type='Interactive', recipient_id=recipient_id, data=data)

    class Utils:
        """
            Utility class for WhatsApp utility methods
        """
        _HUB_SIGNATURE_HEADER_KEY = "x-hub-signature-256"

        def __init__(self, parent) -> None:
            self.parent = parent

        def _pre_process(self, webhook_data: Dict[Any, Any]) -> Dict[Any, Any]:
            """
            Preprocesses the data received from the webhook.

            This method is designed to only be used internally.

            Args:
                webhook_data[dict]: The data received from the webhook
            """
            value_entry = webhook_data["entry"][0]["changes"][0]["value"]
            assert value_entry.get("messaging_product") == "whatsapp"
            return value_entry

        def is_valid_webhook_message(self, webhook_data: Dict) -> bool:
            processed_data = self._pre_process(webhook_data)
            return "messages" in processed_data

        def verify_webhook_verification_challenge(self, mode: str, challenge: str, token: str) -> Union[str, None]:
            if mode == "subscribe" and token == self.parent.config.hub_verification_token:
                return challenge
            return None

        def verify_webhook_payload(self, webhook_payload: Dict, webhook_headers: Dict) -> bool:
            # TODO: perform request header hub signature verification
            if self._HUB_SIGNATURE_HEADER_KEY not in webhook_headers:
                raise Exception("Unsecure webhook payload received")

            return True

        def was_request_successful(self, recipient_id: str, response_data: Dict[str, Any]) -> bool:
            """
            check if the response after sending to whatsapp is valid
            """
            is_whatsapp = response_data.get("messaging_product") == "whatsapp"
            is_same_recipient = recipient_id == response_data.get("contacts")[0].get("wa_id")
            has_msg_id = response_data.get("messages")[0].get("id").startswith("wamid.")

            return is_whatsapp and is_same_recipient and has_msg_id

        def get_response_message_id(self, response_data: Dict[str, Any]) -> Union[str, None]:
            assert response_data.get("messaging_product") == "whatsapp"
            msg_id = response_data.get("messages")[0].get("id")

            if msg_id.startswith("wamid."):
                return msg_id

            return None

        def get_wa_user(self, webhook_data: Dict[Any, Any]) -> Union[WaUser, None]:
            data = self._pre_process(webhook_data)

            if not self.is_valid_webhook_message(webhook_data):
                _logger.critical("Invalid webhook message")
                return None

            user = WaUser()

            if "contacts" in data:
                user.wa_id = data["contacts"][0]["wa_id"]
                user.name = data["contacts"][0]["profile"]["name"]

            if "messages" in data:
                user.msg_id = data["messages"][0]["id"]
                user.timestamp = data["messages"][0]["timestamp"]

            user.validate()

            return user

        def get_delivery(self, webhook_data: Dict[Any, Any]) -> Union[str, None]:
            """
            Extracts the delivery status of the message from the data received from the webhook.
            """
            data = self._pre_process(webhook_data)
            if "statuses" in data:
                return data["statuses"][0]["status"]

        def get_response_structure(self, webhook_data: Dict[Any, Any]) -> Union[ResponseStructure, None]:
            """
            Compute the response body of the message from the data received from the webhook.
            :param webhook_data: WhatsApp webhook data
            :return: ResponseStructure with response type and body
            """
            if self.is_valid_webhook_message(webhook_data):
                data = self._pre_process(webhook_data)
                return MessageUtils(message_data=data.get("messages")[0]).get_structure()

        async def upload_media(self, media_path: str) -> Union[str, None]:
            """
            Asynchronously uploads a media file to the cloud API and returns the ID of the media.

            Args:
                media_path (str): Path of the media to be uploaded.

            REFERENCE:
            https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#
            """
            content_type, _ = mimetypes.guess_type(media_path)
            headers = self.parent.headers.copy()

            try:
                async with AsyncClient() as client, open(os.path.realpath(media_path), 'rb') as file:
                    files = {'file': (os.path.basename(media_path), file, content_type)}
                    data = {
                        'messaging_product': 'whatsapp',
                        'type': content_type
                    }
                    response = await client.post(
                        f"{self.parent.base_url}/{self.parent.config.phone_number_id}/media",
                        headers=headers,
                        files=files,
                        data=data
                    )

                if response.status_code == 200:
                    _logger.info(f"Media {media_path} uploaded!")
                    return response.json().get("id")

                else:
                    _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
                    return None

            except Exception as e:
                _logger.error(f"Exception occurred while uploading media: {str(e)}")
                return None

        async def delete_media(self, media_id: str) -> bool:
            """
            Asynchronously deletes a media from the cloud API.

            Args:
                media_id (str): ID of the media to be deleted.
            """
            async with AsyncClient() as client:
                response = await client.delete(
                    url=f"{self.parent.base_url}/{media_id}",
                    headers=self.parent.headers
                )

            if response.status_code == 200:
                _logger.info(f"Media {media_id} deleted")
                return response.json().get("success")
            else:
                _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
                return False

        async def query_media_url(self, media_id: str) -> Union[str, None]:
            """
            Asynchronously query media URL from a media ID obtained either by manually uploading media or received media.

            Args:
                media_id (str): Media ID of the media.

            Returns:
                str: Media URL, or None if not found or an error occurred.

            """
            async with AsyncClient() as client:
                response = await client.get(
                    url=f"{self.parent.base_url}/{media_id}",
                    headers=self.parent.headers
                )

            if response.status_code == 200:
                result = response.json()
                _logger.info(f"Media URL query result {result}")
                return result.get("url")
            else:
                _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
                return None

        async def download_media(self, media_url: str, mime_type: str, file_path: str = None) -> Union[str, None]:
            """
            Asynchronously download media from a media URL obtained either by manually uploading media or received media.

            Args:
                media_url (str): Media URL of the media.
                mime_type (str): Mime type of the media.
                file_path (str): Path of the file to be downloaded to. Default is "pywce-media-temp".
                                 Do not include the file extension. It will be added automatically.

            Returns:
                str: Path to the downloaded file, or None if there was an error.

            """
            if not mimetypes.guess_extension(mime_type):
                _logger.error(f"Invalid or unsupported MIME type: {mime_type}")
                return None

            from random import randint

            extension = mimetypes.guess_extension(mime_type)
            save_file_here = f"{file_path}.{extension}" if file_path is not None \
                else f"pywce-media-temp-{randint(11, 999999)}.{extension}"

            try:
                async with AsyncClient() as client:
                    response = await client.get(f"{self.parent.base_url}/{media_url}")

                if response.status_code == 200:
                    os.makedirs(os.path.dirname(save_file_here), exist_ok=True)
                    with open(save_file_here, "wb") as f:
                        f.write(response.content)
                    _logger.debug(f"Media downloaded to {save_file_here}")
                    return save_file_here
                else:
                    _logger.critical(f"Failed to download media. Status code: {response.status_code}")
                    return None

            except Exception as e:
                _logger.error(f"Error downloading media to {save_file_here}: {str(e)}")
                return None
