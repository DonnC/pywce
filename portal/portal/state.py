import asyncio
import json
from datetime import datetime
from typing import List, Optional

import reflex as rx

from pywce import pywce_logger
from .constants import ChatRole, TERMINATION_COMMAND, PubSubChannel, RequestChatState
from .model import Message, Chat
from .redis_manager import RedisManager

logger = pywce_logger(__name__, False)

redis_manager = RedisManager()


class ChatState(rx.State):
    message: str = ""
    active_chat: Optional[Chat] = None
    chats: list[Chat]
    current_chat_messages: list[Message]
    is_loading: bool = True

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
        with rx.session() as session:
            if self.active_chat and self.message:
                chat = session.get(Chat, self.active_chat.id)
                chat.last_active = datetime.now()

                await redis_manager.get_instance().publish(
                    channel=PubSubChannel.OUTGOING,
                    message=json.dumps({
                        "type": "TERMINATE" if self.message.lower().strip() == TERMINATION_COMMAND else "MESSAGE",
                        "recipient_id": chat.sender,
                        "message": self.message
                    })
                )

            logger.info(f"Publishing message to channel")

            if self.message.lower() == TERMINATION_COMMAND:
                chat.status = RequestChatState.CLOSED

            new_message = Message(
                sender=ChatRole.ADMIN,
                content=self.message.strip(),
                chat_id=chat.id,
            )

            session.add(new_message)
            session.commit()

            session.refresh(new_message)
            session.refresh(chat)

            logger.info("Updating state after message send")

            self.current_chat_messages.append(new_message)
            self.message = ""
            self.active_chat = chat

    @rx.event
    def load_current_chat_messages(self):
        """
            Load messages for current chat
        """
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
        # TODO: change chat state to OPEN
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
                chat = Chat(sender=sender)
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
            session.add(chat)
            session.commit()

            session.refresh(chat)
            session.refresh(new_message)

            if self.active_chat:
                if chat.id == self.active_chat.id:
                    self.current_chat_messages.insert(0, new_message)

            else:
                self.is_loading = True
                self.load_initial_chats()

    @rx.var(cache=False)
    def get_chats(self) -> List[Chat]:
        return [] if self.chats is None else self.chats

    @rx.var(cache=False)
    def get_messages(self) -> List[Message]:
        return self.current_chat_messages

    @rx.event(background=True)
    async def load_chats_subscribe_webhooks(self):
        async with self:
            self.load_initial_chats()

        logger.debug("Setting webhook pub/sub listener")

        async with redis_manager.get_instance().pubsub() as pubsub:
            while True:
                try:
                    await pubsub.psubscribe(PubSubChannel.INCOMING)

                    wh_msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)

                    if wh_msg is not None:
                        async with self:
                            logger.debug(f"New webhook message: {wh_msg}")

                            message = wh_msg.get("data").decode()
                            msg_data = json.loads(message)

                            self.receive_message(
                                msg_data.get("recipient_id"),
                                msg_data.get("message")
                            )

                except:
                    logger.error(f"Load webhook message error", exc_info=True)

                await asyncio.sleep(0.1)
