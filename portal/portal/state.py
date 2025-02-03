from datetime import datetime
from typing import List, Dict

import reflex as rx

from .constants import ChatRole
from .data import chats
from .model import Message

class SupportState(rx.State):
    message: str = ""
    active_chat: str = ""
    last_active: Dict[str, datetime] = {}  # Store last active times

    @rx.event
    def send_message(self):
        # TODO: Send a message to the user via WhatsApp API
        if self.active_chat and self.message:
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
