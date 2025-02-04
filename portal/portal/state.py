from datetime import datetime
from typing import List, Dict

import reflex as rx

from .constants import ChatRole
from .data import chats
from .model import Message


class WebhookState(rx.State):
    """State to manage webhook data and UI updates."""
    webhook_count: int = 0
    last_webhook_time: str = ""

    @rx.event
    async def update_webhook_stats(self):
        """Update webhook statistics."""
        self.webhook_count += 1
        self.last_webhook_time = str(datetime.now())


class SupportState(rx.State):
    message: str = ""
    active_chat: str = ""
    last_activ = {}  # Store last active times as Dict[str, datetime]

    @rx.event
    def send_message(self):
        # TODO: check for termination command to end session
        if self.active_chat and self.message:
            # TODO: Send a message to the user via WhatsApp API
            new_message = Message(sender=ChatRole.ADMIN, content=self.message.strip())

            if self.active_chat not in chats:
                chats[self.active_chat] = []

            chats[self.active_chat].append(new_message)
            self.message = ""

    @rx.event
    def set_active_chat(self, phone_number: str):
        """
            Set the active chat to display.
            phone_number == chat == wa_id
        """
        self.active_chat = phone_number

    def receive_message(self, phone_number: str, message: str):
        """TODO: Simulate receiving a message from a user."""
        new_message = Message(sender="user", content=message.strip())

        if phone_number not in chats:
            chats[phone_number] = []

        chats[phone_number].append(new_message)

    @rx.var
    def get_chats(self) -> List[str]:
        """Get a list of all active chats."""
        return list(chats.keys())

    @rx.var
    def get_messages(self) -> List[Message]:
        """Get messages for the active chat."""
        return chats.get(self.active_chat, [])
