"""
Cloned from https://github.com/Neurotech-HQ/heyoo

Unofficial python wrapper for the WhatsApp Cloud API.
"""
import mimetypes
import os
from typing import Dict, Any, List, Union

import httpx
from httpx import AsyncClient

from engine_logger import get_engine_logger


class WhatsAppConfig:
    """
        Store whatsapp configs to use in [WhatsApp] class
    """
    token: str
    phone_number_id: str
    version: str


class WhatsApp:
    """
    WhatsApp Object
    """

    def __init__(self, config: WhatsAppConfig):
        """
        Initialize the WhatsApp Object

        Args:
            config[WhatsAppConfig]: config object
        """
        self.config = config
        self.base_url = f"https://graph.facebook.com/{self.config.version}"
        self.url = f"{self.base_url}/{self.config.phone_number_id}/messages"

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.config.token)
        }

        self.logger = get_engine_logger(__name__)

    async def __send_request__(self, message_type: str, recipient_id: str, data: Dict[str, Any]):
        self.logger.info(f"Sending {message_type} to {recipient_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, json=data)

        if response.status_code == 200:
            self.logger.info(f"{message_type.title()} sent to {recipient_id}")
            return response.json()
        else:
            self.logger.info(f"{message_type.title()} not sent to {recipient_id}: {response.status_code}")
            self.logger.error(f"Response: {response.text}")
            return response.json()

    async def send_message(self, message: str, recipient_id: str, recipient_type: str = "individual",
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

        return await self.__send_request__(message_type='Message', recipient_id=recipient_id, data=data)

    async def send_reaction(self, emoji: str, message_id: str, recipient_id: str, recipient_type: str = "individual"):
        """
        Sends a reaction message to a WhatsApp user's message asynchronously.

        Args:
            emoji (str): Emoji to become a reaction to a message. Ex.: '\uD83D\uDE00' (😀)
            message_id (str): Message id for a reaction to be attached to
            recipient_id (str): Phone number of the user with country code without +
            recipient_type (str): Type of the recipient, either individual or group

        Example:
            ```python
            from modules.whatsapp import WhatsApp

            whatsapp = WhatsApp('token', 'phone_number_id')
            whatsapp.send_reaction("\uD83D\uDE00", "wamid.HBgLM...", "5511999999999")
            ```
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "reaction",
            "reaction": {"message_id": message_id, "emoji": emoji},
        }

        return await self.__send_request__(message_type='Reaction', recipient_id=recipient_id, data=data)

    async def send_template(self, template: str, recipient_id: str, components: List[Dict], message_id: str = None,
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
            components (list): List of components to be sent to the user.
            lang (str): Language of the template message, default is "en_US".

        Example:
            >>> from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp("token", "phone_number_id")
            >>> whatsapp.send_template("hello_world", "5511999999999",
            >>>     components=[{"type": "header", "parameters": [{"type": "text", "text": "Header Text"}]}],
            >>>     lang="en_US")
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

        return await self.__send_request__(message_type='Template', recipient_id=recipient_id, data=data)

    async def send_location(self, lat: str, lon: str, name: str, address: str, recipient_id: str,
                            message_id: str = None, ):
        """
        Asynchronously sends a location message to a WhatsApp user.

        Args:
            lat (str): Latitude of the location.
            lon (str): Longitude of the location.
            name (str): Name of the location.
            address (str): Address of the location.
            recipient_id (str): Phone number of the user with country code without +.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp('token', 'phone_number_id')
            >>> whatsapp.send_location("-23.564", "-46.654", "My Location", "Rua dois, 123", "5511999999999")
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

        return await self.__send_request__(message_type='Location', recipient_id=recipient_id, data=data)

    async def send_image(
            self,
            image: str,
            recipient_id: str,
            recipient_type: str = "individual",
            caption: str = None,
            link: bool = True,
            message_id: str = None
    ):
        """
        Asynchronously sends an image message to a WhatsApp user. The image can be sent by specifying either
        an image ID or a link to the image.

        Args:
            image (str): Image ID or link to the image.
            recipient_id (str): Phone number of the user with country code without +.
            recipient_type (str): Type of the recipient, either individual or group.
            caption (str, optional): Caption for the image.
            link (bool): True if sending by image ID, False if sending by image link.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp('token', 'phone_number_id')
            >>> whatsapp.send_image("https://i.imgur.com/Fh7XVYY.jpeg", "5511999999999")
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "image",
            "image": {"link": image, "caption": caption} if link else {"id": image, "caption": caption}
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self.__send_request__(message_type='Image', recipient_id=recipient_id, data=data)

    async def send_sticker(self, sticker: str, recipient_id: str, recipient_type="individual", link: bool = True,
                           message_id: str = None):
        """
        Asynchronously sends a sticker message to a WhatsApp user.

        There are two ways to send a sticker message to a user, either by passing the sticker id or by passing the sticker link.
        Sticker id is the id of the sticker uploaded to the cloud API.

        Args:
            sticker (str): Sticker id or link of the sticker.
            recipient_id (str): Phone number of the user with country code without +.
            recipient_type (str): Type of the recipient, either individual or group.
            link (bool): Whether to send a sticker id or a sticker link, True means that the sticker is an id, False means the sticker is a link.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp('token', 'phone_number_id')
            >>> whatsapp.send_sticker("https://link_to_sticker_image.png", "5511999999999", link=True)
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "sticker",
            "sticker": {"link": sticker} if link else {"id": sticker},
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self.__send_request__(message_type='Sticker', recipient_id=recipient_id, data=data)

    async def send_audio(self, audio: str, recipient_id: str, link=True, message_id: str = None):
        """
        Asynchronously sends an audio message to a WhatsApp user. Audio messages can be sent by either passing the audio ID or by passing the audio link.

        Args:
            audio (str): Audio ID or link of the audio.
            recipient_id (str): Phone number of the user with country code without +.
            link (bool): Whether to send an audio ID or an audio link, True means that the audio is an ID, False means that the audio is a link.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp()
            >>> whatsapp.send_audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "5511999999999")
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "audio",
            "audio": {"link": audio} if link else {"id": audio},
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self.__send_request__(message_type='Audio', recipient_id=recipient_id, data=data)

    async def send_video(self, video: str, recipient_id: str, caption: str = None, link: bool = True,
                         message_id: str = None):
        """
        Asynchronously sends a video message to a WhatsApp user. Video messages can either be sent by passing the video ID or by passing the video link.

        Args:
            video (str): Video ID or link of the video.
            recipient_id (str): Phone number of the user with country code without +.
            caption (str, optional): Caption of the video.
            link (bool): Whether to send a video ID or a video link, True means that the video is an ID, False means that the video is a link.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp()
            >>> whatsapp.send_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "5511999999999")
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "video",
            "video": {"link": video, "caption": caption} if link else {"id": video, "caption": caption},
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self.__send_request__(message_type='Video', recipient_id=recipient_id, data=data)

    async def send_document(self, document: str, recipient_id: str, caption: str = None, link: bool = True,
                            filename: str = None, message_id: str = None):
        """
        Asynchronously sends a document message to a WhatsApp user. Documents can either be sent by passing the document ID or by passing the document link.

        Args:
            document (str): Document ID or link of the document.
            recipient_id (str): Phone number of the user with country code without +.
            caption (str, optional): Caption of the document.
            link (bool): Whether to send a document ID or a document link, True means the document is an ID, False means the document is a link.
            filename (str, optional): Name of the file if sending by link.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp()
            >>> whatsapp.send_document("https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", "5511999999999")
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "document",
            "document": {"link": document, "caption": caption, "filename": filename} if link
            else {"id": document, "caption": caption}
        }

        if message_id is not None:
            data["context"] = {"message_id": message_id}

        return await self.__send_request__(message_type='Document', recipient_id=recipient_id, data=data)

    async def send_contacts(self, contacts: List[Dict[Any, Any]], recipient_id: str, message_id:str=None):
        """
        Asynchronously sends a list of contacts to a WhatsApp user.

        Args:
            contacts (List[Dict[Any, Any]]): List of contacts to send, structured according to the WhatsApp API requirements.
            recipient_id (str): Phone number of the user with country code without +.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp()
            >>> contacts = [{
                "addresses": [{
                    "street": "STREET",
                    "city": "CITY",
                    "state": "STATE",
                    "zip": "ZIP",
                    "country": "COUNTRY",
                    "country_code": "COUNTRY_CODE",
                    "type": "HOME"
                    }],
                ...
                }]
            >>> whatsapp.send_contacts(contacts, "5511999999999")

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

        return await self.__send_request__(message_type='Contacts', recipient_id=recipient_id, data=data)

    async def upload_media(self, media: str) -> Union[Dict[Any, Any], None]:
        """
        Asynchronously uploads a media file to the cloud API and returns the ID of the media.

        Args:
            media (str): Path of the media to be uploaded.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp()
            >>> whatsapp.upload_media("/path/to/media")

        REFERENCE:
        https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#
        """
        content_type, _ = mimetypes.guess_type(media)
        headers = self.headers.copy()
        self.logger.info(f"Uploading media {media}")

        try:
            async with AsyncClient() as client, open(os.path.realpath(media), 'rb') as file:
                files = {'file': (os.path.basename(media), file, content_type)}
                data = {
                    'messaging_product': 'whatsapp',
                    'type': content_type
                }
                response = await client.post(
                    f"{self.base_url}/{self.config.phone_number_id}/media",
                    headers=headers,
                    files=files,
                    data=data
                )

            if response.status_code == 200:
                self.logger.info(f"Media {media} uploaded")
                return response.json()
            else:
                self.logger.info(f"Error uploading media {media}")
                self.logger.info(f"Status code: {response.status_code}")
                self.logger.info(f"Response: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Exception occurred while uploading media: {str(e)}")
            return None

    async def delete_media(self, media_id: str) -> Union[Dict[Any, Any], None]:
        """
        Asynchronously deletes a media from the cloud API.

        Args:
            media_id (str): ID of the media to be deleted.
        """
        self.logger.info(f"Deleting media {media_id}")
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/{media_id}", headers=self.headers)

        if response.status_code == 200:
            self.logger.info(f"Media {media_id} deleted")
            return response.json()
        else:
            self.logger.info(f"Error deleting media {media_id}: {response.status_code}")
            self.logger.error(f"Response: {response.text}")
            return None

    async def mark_as_read(self, message_id: str) -> Dict[Any, Any]:
        """
        Asynchronously marks a message as read using the WhatsApp Cloud API.

        Args:
            message_id (str): ID of the message to be marked as read.

        Returns:
            Dict[Any, Any]: Response from the API.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp()
            >>> whatsapp.mark_as_read("message_id")
        """
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        return await self.__send_request__(message_type='MarkAsRead', recipient_id=message_id, data=data)

    def __create_button__(self, button: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Method to create a button object to be used in the send_message method.

        This is method is designed to only be used internally by the send_button method.

        Args:
               button[dict]: A dictionary containing the button data
        """
        data = {"type": "list", "action": button.get("action")}
        if button.get("header"):
            data["header"] = {"type": "text", "text": button.get("header")}
        if button.get("body"):
            data["body"] = {"text": button.get("body")}
        if button.get("footer"):
            data["footer"] = {"text": button.get("footer")}
        return data

    async def send_button(self, button: Dict[Any, Any], recipient_id: str) -> Dict[Any, Any]:
        """
        Asynchronously sends an interactive buttons message to a WhatsApp user.

        Args:
            button (dict): A dictionary containing the button data (rows-title may not exceed 20 characters).
            recipient_id (str): Phone number of the user with country code without +.

        Check https://github.com/Neurotech-HQ/heyoo#sending-interactive-reply-buttons for an example.
        """
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": self.__create_button__(button),
        }

        self.logger.info(f"Sending buttons to {recipient_id}")
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, json=data)

        if response.status_code == 200:
            self.logger.info(f"Buttons sent to {recipient_id}")
            return response.json()
        else:
            self.logger.info(f"Buttons not sent to {recipient_id}: {response.status_code}")
            self.logger.error(f"Response: {response.text}")
            return response.json()

    async def send_reply_button(self, button: Dict[Any, Any], recipient_id: str) -> Dict[Any, Any]:
        """
        Asynchronously sends an interactive reply buttons [menu] message to a WhatsApp user.

        Args:
            button (dict): A dictionary containing the button data.
            recipient_id (str): Phone number of the user with country code without +.

        Note:
            The maximum number of buttons is 3; more than 3 buttons will raise an error.
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": button,
        }

        self.logger.info(f"Sending reply buttons to {recipient_id}")
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, json=data)

        if response.status_code == 200:
            self.logger.info(f"Reply buttons sent to {recipient_id}")
            return response.json()
        else:
            self.logger.info(f"Reply buttons not sent to {recipient_id}: {response.status_code}")
            self.logger.error(f"Response: {response.text}")
            return response.json()

    async def query_media_url(self, media_id: str) -> Union[str, None]:
        """
        Asynchronously query media URL from a media ID obtained either by manually uploading media or received media.

        Args:
            media_id (str): Media ID of the media.

        Returns:
            str: Media URL, or None if not found or an error occurred.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.query_media_url("media_id")
        """
        self.logger.info(f"Querying media URL for {media_id}")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/{media_id}", headers=self.headers)

        if response.status_code == 200:
            self.logger.info(f"Media URL queried for {media_id}")
            return response.json().get("url")
        else:
            self.logger.info(f"Media URL not queried for {media_id}: {response.status_code}")
            self.logger.info(f"Response: {response.text}")
            return None

    async def download_media(self, media_url: str, mime_type: str, file_path: str = "temp") -> Union[str, None]:
        """
        Asynchronously download media from a media URL obtained either by manually uploading media or received media.

        Args:
            media_url (str): Media URL of the media.
            mime_type (str): Mime type of the media.
            file_path (str): Path of the file to be downloaded to. Default is "temp".
                             Do not include the file extension. It will be added automatically.

        Returns:
            str: Path to the downloaded file, or None if there was an error.

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.download_media("https://example.com/media_url", "image/jpeg")
            >>> whatsapp.download_media("https://example.com/media_url", "video/mp4", "path/to/file") #do not include the file extension
        """
        extension = mime_type.split("/")[1].split(";")[0].strip()
        save_file_here = f"{file_path}.{extension}" if file_path else f"temp.{extension}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(media_url)

            if response.status_code == 200:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(save_file_here), exist_ok=True)
                with open(save_file_here, "wb") as f:
                    f.write(response.content)
                self.logger.info(f"Media downloaded to {save_file_here}")
                return save_file_here
            else:
                self.logger.error(f"Failed to download media. Status code: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error downloading media to {save_file_here}: {str(e)}")
            return None

    def preprocess(self, data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Preprocesses the data received from the webhook.

        This method is designed to only be used internally.

        Args:
            data[dict]: The data received from the webhook
        """
        return data["entry"][0]["changes"][0]["value"]

    def is_message(self, data: Dict[Any, Any]) -> bool:
        """is_message checks if the data received from the webhook is a message.

        Args:
            data (Dict[Any, Any]): The data received from the webhook

        Returns:
            bool: True if the data is a message, False otherwise
        """
        data = self.preprocess(data)
        if "messages" in data:
            return True
        else:
            return False

    def get_mobile(self, data: Dict[Any, Any]) -> Union[str, None]:
        """
        Extracts the mobile number of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            str: The mobile number of the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> mobile = whatsapp.get_mobile(data)
        """
        data = self.preprocess(data)
        if "contacts" in data:
            return data["contacts"][0]["wa_id"]

    def get_name(self, data: Dict[Any, Any]) -> Union[str, None]:
        """
        Extracts the name of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            str: The name of the sender
        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> mobile = whatsapp.get_name(data)
        """
        contact = self.preprocess(data)
        if contact:
            return contact["contacts"][0]["profile"]["name"]

    def get_message(self, data: Dict[Any, Any]) -> Union[str, None]:
        """
        Extracts the text message of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            str: The text message received from the sender
        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> message = message.get_message(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            return data["messages"][0]["text"]["body"]

    def get_message_id(self, data: Dict[Any, Any]) -> Union[str, None]:
        """
        Extracts the message id of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            str: The message id of the sender
        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> message_id = whatsapp.get_message_id(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            return data["messages"][0]["id"]

    def get_message_timestamp(self, data: Dict[Any, Any]) -> Union[str, None]:
        """ "
        Extracts the timestamp of the message from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            str: The timestamp of the message
        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.get_message_timestamp(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            return data["messages"][0]["timestamp"]

    def get_interactive_response(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """
         Extracts the response of the interactive message from the data received from the webhook.

         Args:
            data[dict]: The data received from the webhook
        Returns:
            dict: The response of the interactive message

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> response = whatsapp.get_interactive_response(data)
            >>> interactive_type = response.get("type")
            >>> message_id = response[interactive_type]["id"]
            >>> message_text = response[interactive_type]["title"]
        """
        data = self.preprocess(data)
        if "messages" in data:
            if "interactive" in data["messages"][0]:
                return data["messages"][0]["interactive"]

    def get_location(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """
        Extracts the location of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook

        Returns:
            dict: The location of the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.get_location(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            if "location" in data["messages"][0]:
                return data["messages"][0]["location"]

    def get_image(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """ "
        Extracts the image of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            dict: The image_id of an image sent by the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> image_id = whatsapp.get_image(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            if "image" in data["messages"][0]:
                return data["messages"][0]["image"]

    def get_document(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """ "
        Extracts the document of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook
        Returns:
            dict: The document_id of an image sent by the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> document_id = whatsapp.get_document(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            if "document" in data["messages"][0]:
                return data["messages"][0]["document"]

    def get_audio(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """
        Extracts the audio of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook

        Returns:
            dict: The audio of the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.get_audio(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            if "audio" in data["messages"][0]:
                return data["messages"][0]["audio"]

    def get_video(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """
        Extracts the video of the sender from the data received from the webhook.

        Args:
            data[dict]: The data received from the webhook

        Returns:
            dict: Dictionary containing the video details sent by the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.get_video(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            if "video" in data["messages"][0]:
                return data["messages"][0]["video"]

    def get_message_type(self, data: Dict[Any, Any]) -> Union[str, None]:
        """
        Gets the type of the message sent by the sender from the data received from the webhook.


        Args:
            data [dict]: The data received from the webhook

        Returns:
            str: The type of the message sent by the sender

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.get_message_type(data)
        """
        data = self.preprocess(data)
        if "messages" in data:
            return data["messages"][0]["type"]

    def get_delivery(self, data: Dict[Any, Any]) -> Union[Dict, None]:
        """
        Extracts the delivery status of the message from the data received from the webhook.
        Args:
            data [dict]: The data received from the webhook

        Returns:
            dict: The delivery status of the message and message id of the message
        """
        data = self.preprocess(data)
        if "statuses" in data:
            return data["statuses"][0]["status"]

    def changed_field(self, data: Dict[Any, Any]) -> str:
        """
        Helper function to check if the field changed in the data received from the webhook.

        Args:
            data [dict]: The data received from the webhook

        Returns:
            str: The field changed in the data received from the webhook

        Example:
            >>>  from modules.whatsapp import WhatsApp
            >>> whatsapp = WhatsApp(token, phone_number_id)
            >>> whatsapp.changed_field(data)
        """
        return data["entry"][0]["changes"][0]["field"]
