import asyncio
from datetime import datetime
from typing import List, Optional

import reflex as rx

from pywce import pywce_logger
from .chatbot.dependencies import get_engine_instance
from .constants import ChatRole, TERMINATION_COMMAND
from .data import fetch_global, clear_global_entry, evict_global
from .model import Message, Chat

logger = pywce_logger(__name__)


class ChatState(rx.State):
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
            logger.info(f"Loaded {len(self.chats)} chats!")

    @rx.event
    async def send_message(self):
        engine_obj = get_engine_instance()

        if self.active_chat and self.message:
            if self.message.lower() == TERMINATION_COMMAND:
                logger.info("[-] Received termination command")
                engine_obj.ls_terminate(self.active_chat.sender)
                evict_global(self.active_chat.sender)
                return

            result = await engine_obj.ls_send_message(
                recipient_id=self.active_chat.sender,
                message=self.message,
            )

            logger.debug(f"Channel result: {result}")

            if result:
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
    def receive_message(self, sender: str = None, message: str = None):
        """Handle incoming webhook message"""
        logger.info(f"Received message from {sender}: {message}")

        if sender is None:
            return

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

            if self.active_chat:
                if str(chat.id) == self.active_chat.id:
                    session.refresh(new_message)
                    self.current_chat_messages.insert(0, new_message)

    @rx.var(cache=False)
    def get_chats(self) -> List[Chat]:
        return [] if self.chats is None else self.chats

    @rx.var(cache=False)
    def get_messages(self) -> List[Message]:
        return self.current_chat_messages

    @rx.event(background=True)
    async def poll_new_chat_messages(self):
        logger.info(f"Bg, poll new chat messages")
        async with self:
            self.load_initial_chats()

        queue = fetch_global()

        while True:
            logger.info(f"Message queue: {queue}")

            # loop thru global data and pass args
            async with self:
                for chat_user, messages in queue.items():
                    for msg in messages:
                        logger.info(f"Processing msg: {chat_user} | {msg}")
                        self.receive_message(chat_user, msg)

                    clear_global_entry(chat_user)

            await asyncio.sleep(5)
