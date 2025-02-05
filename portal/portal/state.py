from datetime import datetime
from typing import List, Optional

import reflex as rx

from .constants import ChatRole, TERMINATION_COMMAND
from .model import Message, Chat


class SupportState(rx.State):
    message: str = ""
    active_chat: Optional[Chat] = None
    chats: list[Chat]
    current_chat_messages: list[Message]
    is_loading: bool = True

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.load_initial_chats()

    @rx.event
    def load_initial_chats(self):
        with rx.session() as session:
            chats = session.exec(
                Chat.select().order_by(Chat.last_active.desc())
            ).all()
            self.chats = chats
            self.is_loading = False
            print(f"Loaded {len(self.chats)} chats!")

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
                chat.last_active = datetime.now()

                new_message = Message(
                    sender=ChatRole.ADMIN,
                    content=self.message.strip(),
                    chat_id=self.active_chat.id,
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
                        Message.chat == self.active_chat
                    ).order_by(Message.timestamp)
                ).all()
                self.current_chat_messages = messages

    @rx.event
    def set_active_chat(self, chat: Chat):
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

            new_message = Message(
                content=message.strip(),
                sender=ChatRole.USER,
                chat=chat
            )
            session.add(new_message)
            session.commit()

            if str(chat.id) == self.active_chat.id:
                session.refresh(new_message)
                self.current_chat_messages.insert(0, new_message)

    @rx.var
    def get_chats(self) -> List[Chat]:
        return [] if self.chats is None else self.chats

    @rx.var(cache=True)
    def get_messages(self) -> List[Message]:
        return self.current_chat_messages
