from datetime import datetime
from typing import List

import reflex as rx

from .constants import ChatRole, TERMINATION_COMMAND
from .model import Message, Chat


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
    active_chat: Chat = None
    chats: list[Chat]
    current_chat_messages: list[Message]
    is_loading: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_initial_chats()

    @rx.event
    def load_initial_chats(self):
        with rx.session() as session:
            chats = session.exec(
                Chat.select().order_by(Chat.last_active.desc())
            ).all()
            self.chats = chats
            self.is_loading = False
            print("Loaded chats: ", self.chats)

    @rx.event
    def send_message(self):
        if self.active_chat and self.message:
            if self.message.lower() == TERMINATION_COMMAND:
                # TODO: implement session termination
                print("[-] Received termination command")
                pass

            # TODO: Send a message to the user via WhatsApp API
            with rx.session() as session:
                chat = session.get(Chat, self.active_chat.id)
                new_message = Message(
                    sender=ChatRole.ADMIN,
                    content=self.message.strip(),
                    chat=chat
                )

                session.add(new_message)
                session.commit()
                session.refresh(new_message)

                self.current_chat_messages.append(new_message)
                self.message = ""

    @rx.event
    def load_current_chat_messages(self):
        """Load messages for current chat"""
        if self.active_chat:
            with rx.session() as session:
                messages = session.exec(
                    Message.select().where(
                        Message.chat_id == self.active_chat.id
                    ).order_by(Message.timestamp)
                ).all()
                self.current_chat_messages = messages

    @rx.event
    def set_active_chat(self, chat: Chat):
        """Set the active chat to display & load messages"""
        self.active_chat = chat
        self.load_current_chat_messages()

    @rx.event
    def receive_message(self, sender: str, message: str):
        """Handle incoming webhook message"""
        with rx.session() as session:
            chat = session.exec(Chat.select().where(Chat.sender == sender)).first()

            if not chat:
                chat = Chat(
                    sender=sender,
                    status=1
                )
                session.add(chat)
                session.commit()
                session.refresh(chat)
                self.chats.append(chat)

            chat.last_active = datetime.now()

            # Create new message
            new_message = Message(
                content=message.strip(),
                sender=ChatRole.USER,
                chat=chat
            )
            session.add(new_message)
            session.commit()

            # Update UI if this is the active chat
            if str(chat.id) == self.active_chat.id:
                session.refresh(new_message)
                self.current_chat_messages.insert(0, new_message)

    @rx.var
    def get_chats(self) -> List[Chat]:
        """Get a list of all active chats."""
        return [] if self.chats is None else self.chats

    @rx.var(cache=True)
    def get_messages(self) -> List[Message]:
        """Get messages for the active chat."""
        return self.current_chat_messages
