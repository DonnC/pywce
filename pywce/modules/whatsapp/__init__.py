"""
Originally cloned from https://github.com/Neurotech-HQ/heyoo PR by
https://github.com/oca159/heyoo/tree/main

Unofficial python wrapper for the WhatsApp Cloud API.
"""
import json
import logging
import mimetypes
import os
from base64 import b64decode, b64encode
from collections.abc import Callable
from dataclasses import dataclass
from typing import Dict, Any, List, Union, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from httpx import Client

from pywce.modules.whatsapp.config import WhatsAppConfig
from pywce.modules.whatsapp.message_utils import MessageUtils
from pywce.modules.whatsapp.model import MessageTypeEnum, WaUser, ResponseStructure
from pywce.src.exceptions import EngineClientException, HookException, FlowEndpointException

_logger = logging.getLogger(__name__)


@dataclass
class FlowEndpointPayload:
    """
    Actual flow endpoint payload. Can be
    1. Data exchange
           {
                "version": "<VERSION>",
                "action": "<ACTION_NAME>",
                "screen": "<SCREEN_NAME>",
                "data": {
                  "prop_1": "value_1",
                   …
                  "prop_n": "value_n"
                },
               "flow_token": "<FLOW-TOKEN>"
            }
    2. Ping
        {
            "version": "3.0",
            "action": "ping"
        }
    3. Error message
        {
            "version": "<VERSION>",
            "flow_token": "<FLOW-TOKEN>",
            "action": "data_exchange | INIT",
            "data": {
                "error": "<ERROR-KEY>",
                "error_message": "<ERROR-MESSAGE>"
            }
        }
    """
    version: str
    action: str
    screen: Optional[str] = None
    flow_token: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class FlowEndpointResponse:
    payload: FlowEndpointPayload
    aes_key: bytes
    iv: bytes


class WhatsApp:
    """
    WhatsApp Object
    """

    INVALID_SIGNATURE_HTTP_CODE: int = 432
    INVALID_FLOW_TOKEN_HTTP_CODE: int = 427
    CHANGED_PUBLIC_KEY_HTTP_CODE: int = 421

    INIT_FLOW_ACTION = 'INIT'
    BACK_FLOW_ACTION = 'BACK'
    PING_FLOW_ACTION = 'ping'
    DATA_EXCHANGE_FLOW_ACTION = 'data_exchange'

    FLOW_ENDPOINT_ACK_ERROR_PAYLOAD = {"data": {"acknowledged": True}}
    FLOW_ENDPOINT_PING_PAYLOAD = {"data": {"status": "active"}}

    def __init__(self,
                 whatsapp_config: WhatsAppConfig,
                 on_send_listener: Optional[Callable] = None,
                 flow_endpoint_processor: Optional[Callable] = None
                 ):
        """
        Initialize the WhatsApp Object

        Args:
            config[WhatsAppConfig]: config object
        """
        self.config = whatsapp_config
        self.listener = on_send_listener
        self.endpoint_processor = flow_endpoint_processor
        self.base_url = f"https://graph.facebook.com/{self.config.version}"
        self.url = f"{self.base_url}/{self.config.phone_number_id}/messages"

        if self.config.use_emulator is True:
            self.url = self.config.emulator_url

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.token}"
        }
        self.util = self._Utils(self)

    def _send_request(self, message_type: str, recipient_id: str, data: Dict[str, Any]):
        """
        Send a request to the official WhatsApp API

        :param message_type:
        :param recipient_id:
        :param data:
        :return:
        """

        _logger.debug(f"Sending {message_type} to {recipient_id}")

        try:
            with Client() as client:
                response = client.post(self.url, headers=self.headers, json=data)

            if response.status_code == 200:
                return response.json()

            else:
                _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
                return response.json()

        except Exception as e:
            _logger.error(f"Error sending {message_type} to {recipient_id}: {str(e)}")

        finally:
            if self.listener:
                self.listener()

    def send_message(self, recipient_id: str, message: str, recipient_type: str = "individual",
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

        return self._send_request(message_type='Message', recipient_id=recipient_id, data=data)

    def send_reaction(self, recipient_id: str, emoji: str, message_id: str, recipient_type: str = "individual"):
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

        return self._send_request(message_type='Reaction', recipient_id=recipient_id, data=data)

    def send_template(self, recipient_id: str, template: str, components: List[Dict], message_id: str = None,
                      lang: str = "en_US"):
        """
        Asynchronously sends a templates message to a WhatsApp user. Templates can be:
            1. Text templates
            2. Media based templates
            3. Interactive templates
        You can customize the templates message by passing a dictionary of components.
        Find available components in the documentation:
        https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates

        Args:
            template (str): Template name to be sent to the user.
            recipient_id (str): Phone number of the user with country code without +.
            message_id: if replying to a message, include the previous message id here
            components (list): List of components to be sent to the user.
            lang (str): Language of the templates message, default is "en_US".
        """

        assert len(components) <= 0, "Template components list cannot be empty"

        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "templates",
        }

        template_data = {
            "name": template,
            "language": {"code": lang},
            "components": components,
        }

        data["templates"] = template_data

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return self._send_request(message_type='Template', recipient_id=recipient_id, data=data)

    def send_location(self, recipient_id: str, lat: str, lon: str, name: str = None, address: str = None,
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

        return self._send_request(message_type='Location', recipient_id=recipient_id, data=data)

    def request_location(self, recipient_id: str, message: str, message_id: str = None):
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

        return self._send_request(message_type='RequestLocation', recipient_id=recipient_id, data=data)

    def send_media(
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

        return self._send_request(message_type=media_type.name.title(), recipient_id=recipient_id, data=data)

    def send_contacts(self, recipient_id: str, contacts: List[Dict[Any, Any]], message_id: str = None):
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

        return self._send_request(message_type='Contacts', recipient_id=recipient_id, data=data)

    def mark_as_read(self, message_id: str) -> Dict[Any, Any]:
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

        return self._send_request(message_type='MarkAsRead', recipient_id=message_id, data=data)

    def send_interactive(self, recipient_id: str, payload: Dict[Any, Any], message_id: str = None):
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

        return self._send_request(message_type='Interactive', recipient_id=recipient_id, data=data)

    class _Utils:
        """
            Utility class for WhatsApp utility methods

            WhatsApp flows endpoint ref: https://medium.com/@nijmehar16/develop-a-chatbot-using-whatsapp-flows-and-integrate-it-with-your-backend-cf61142aca2e
        """
        _HUB_SIGNATURE_HEADER_KEY = "x-hub-signature-256"
        _MEDIA_DIR = "pywce_downloads"
        _TAG_LENGTH_BYTES = 16

        def __init__(self, parent) -> None:
            self.parent: "WhatsApp" = parent

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

        def webhook_challenge(self, mode: str, challenge: str, token: str) -> Union[str, None]:
            if mode == "subscribe" and token == self.parent.config.hub_verification_token:
                return challenge
            return None

        def bytes_to_dict(self, payload: bytes) -> dict:
            payload_str = payload.decode("utf-8")
            return json.loads(payload_str)

        def decrypt_flow_payload(self, encrypted_flow_payload: dict) -> Optional[FlowEndpointResponse]:
            """
            Decrypts the incoming WhatsApp Flow request payload.
            """
            try:
                encrypted_flow_data_b64 = encrypted_flow_payload.get('encrypted_flow_data')
                encrypted_aes_key_b64 = encrypted_flow_payload.get('encrypted_aes_key')
                initial_vector_b64 = encrypted_flow_payload.get('initial_vector')

                flow_data = b64decode(encrypted_flow_data_b64)
                iv = b64decode(initial_vector_b64)

                pwd: Optional[bytes] = None
                if self.parent.config.private_key_pwd is not None:
                    pwd = self.parent.config.private_key_pwd.encode("utf-8")

                # Decrypt the AES encryption key
                encrypted_aes_key = b64decode(encrypted_aes_key_b64)
                private_key = serialization.load_pem_private_key(
                    self.parent.config.private_key.encode('utf-8'),
                    password=pwd
                )
                aes_key = private_key.decrypt(
                    encrypted_aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                # Decrypt the Flow data
                encrypted_flow_data_body = flow_data[:-self._TAG_LENGTH_BYTES]
                encrypted_flow_data_tag = flow_data[-self._TAG_LENGTH_BYTES:]

                decryptor = Cipher(
                    algorithms.AES(aes_key),
                    modes.GCM(iv, encrypted_flow_data_tag)
                ).decryptor()

                decrypted_data_bytes = decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
                decrypted_data = json.loads(decrypted_data_bytes.decode("utf-8"))

                config_response = FlowEndpointResponse(
                    payload=FlowEndpointPayload(**decrypted_data),
                    aes_key=aes_key,
                    iv=iv
                )

                return config_response

            except Exception as e:
                raise FlowEndpointException(
                    message=f"Failed to decrypt flow payload: {str(e)}",
                    data=self.parent.CHANGED_PUBLIC_KEY_HTTP_CODE
                )

        def encrypt_flow_payload(self, response_payload: dict, config: FlowEndpointResponse) -> str:
            """
            Encrypts the response payload before sending it back to WhatsApp.
            """
            try:
                # Flip the initialization vector
                flipped_iv = bytearray()
                for byte in config.iv:
                    flipped_iv.append(byte ^ 0xFF)

                # Encrypt the response data
                encryptor = Cipher(
                    algorithms.AES(config.aes_key),
                    modes.GCM(bytes(flipped_iv))
                ).encryptor()

                encrypted_response_bytes = encryptor.update(
                    json.dumps(response_payload).encode("utf-8")) + encryptor.finalize()
                full_encrypted_data = encrypted_response_bytes + encryptor.tag

                return b64encode(full_encrypted_data).decode("utf-8")

            except Exception as e:
                raise FlowEndpointException(
                    message="Failed to encrypt flow payload",
                    data=self.parent.CHANGED_PUBLIC_KEY_HTTP_CODE
                )

        def create_final_flow_response(self, flow_token: str, params: dict=None) -> dict:
            return {
                "screen": "SUCCESS",
                "data": {
                    "extension_message_response": {
                        "params": {
                            "flow_token": flow_token,
                            **params
                        }
                    }
                }
            }

        def flow_endpoint_handler(self, flow_payload: dict) -> str:
            """
                Call the configured flow endpoint processor,
                the callable should accept one argument of type FlowEndpointPayload.

            :param flow_payload: raw request payload with encrypted data
            :return: Encrypted flow payload as a str
            :rtype: str
            :raise FlowEndpointException
            """
            try:
                if self.parent.endpoint_processor is None:
                    raise HookException(message="Flow endpoint callable not defined")

                flow_response = self.decrypt_flow_payload(flow_payload)

                response = self.parent.endpoint_processor(flow_response.payload)

                _logger.debug("Flow endpoint processor response: %s", response)

                if response.template_body.flow_payload is None:
                    raise FlowEndpointException(message="Flow handler callback did not return a valid response")

                return self.encrypt_flow_payload(response.template_body.flow_payload, flow_response)

            except FlowEndpointException as fee:
                _logger.error("Error processing flow endpoint", exc_info=True)
                raise fee

            except Exception as e:
                _logger.error("Flow endpoint handler error", exc_info=True)
                raise FlowEndpointException(message="Failed to process flow endpoint request")

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

            user.wa_validator()

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

        def upload_media(self, media_path: str) -> Union[str, None]:
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
                with Client() as client, open(os.path.realpath(media_path), 'rb') as file:
                    files = {'file': (os.path.basename(media_path), file, content_type)}
                    data = {
                        'messaging_product': 'whatsapp',
                        'type': content_type
                    }

                    response = client.post(
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

            finally:
                if self.parent.listener:
                    self.parent.listener()

        def delete_media(self, media_id: str) -> bool:
            """
            Asynchronously deletes a media from the cloud API.

            Args:
                media_id (str): ID of the media to be deleted.
            """
            with Client() as client:
                response = client.delete(
                    url=f"{self.parent.base_url}/{media_id}",
                    headers=self.parent.headers
                )

            if response.status_code == 200:
                _logger.info(f"Media {media_id} deleted")
                return response.json().get("success")
            else:
                _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
                return False

        def query_media_url(self, media_id: str) -> Union[str, None]:
            """
            Asynchronously query media URL from a media ID obtained either by manually uploading media or received media.

            Args:
                media_id (str): Media ID of the media.

            Returns:
                str: Media URL, or None if not found or an error occurred.

            """
            with Client() as client:
                response = client.get(
                    url=f"{self.parent.base_url}/{media_id}",
                    headers=self.parent.headers
                )

            if response.status_code == 200:
                result = response.json()
                _logger.debug(f"Media URL query result {result}")
                return result.get("url")
            else:
                _logger.critical(f"Code: {response.status_code} | Response: {response.text}")
                return None

        def download_media(self, media_url: str, filename: str, download_dir: str = None) -> Union[str, None]:
            """
            Asynchronously download media from a media URL obtained either by manually uploading media or received media.

            Args:
                media_url (str): Media URL of the media.
                filename (str): Media filename with ext e.g file.png
                download_dir (str): Path of the file to be downloaded to. Default is "pywce-media-temp".
            Returns:
                str: Path to the downloaded file, or None if there was an error.
            """
            from random import randint
            folder = self._MEDIA_DIR if download_dir is None else download_dir
            save_file_here = os.path.join(folder, filename)

            if os.path.isfile(save_file_here):
                filename = f"dup_rand{randint(11, 99)}_{filename}"
                save_file_here = os.path.join(folder, filename)

            try:
                with Client() as client:
                    response = client.get(
                        url=media_url,
                        headers=self.parent.headers
                    )

                if response.status_code == 200:
                    os.makedirs(folder, exist_ok=True)

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

            finally:
                if self.parent.listener:
                    self.parent.listener()

        def download_flow_media(self, flow_media_payload: Dict, download_dir: str = None):
            """
            Download media files uploaded on WhatsApp flows
            [
                {'id': 5868146111.., 'mime_type': 'image/jpeg', 'sha256': 'CiXteED..', 'file_name': '4c631dab-...jpg'},
                {'id': 1571385113.., 'mime_type': 'image/jpeg', 'sha256': 'lV..', 'file_name': '5d70f3e...jpg'}
            ]

            Args:
                flow_media_payload (dict): A single dict entry of uploaded media
                download_dir (str): Path of the file to be downloaded to. Default is "pywce_downloads".

            Returns:
                str: path of the downloaded file, or None if there was an error.
            """

            media_url = self.query_media_url(flow_media_payload.get("id"))

            if media_url is None:
                raise EngineClientException(f"Failed to query media file url")

            downloaded_path = self.download_media(media_url, flow_media_payload.get("file_name"), download_dir)

            if downloaded_path is None:
                raise EngineClientException(f"Failed to download file for media id: {flow_media_payload.get('id')}")

            return downloaded_path
