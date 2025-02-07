import asyncio
import json
import sys
from datetime import datetime
from typing import List, Optional

import reflex as rx

from pywce import pywce_logger
from .constants import ChatRole, TERMINATION_COMMAND, PubSubChannel, RequestChatState
from .model import Message, Chat
from .redis_manager import RedisManager

logger = pywce_logger(__name__)

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
        if self.active_chat and self.message:
            if self.message.lower() == TERMINATION_COMMAND:
                logger.info("[-] Received termination command")
                await redis_manager.get_instance().publish(
                    channel=PubSubChannel.OUTGOING,
                    message=json.dumps({"type": "TERMINATE"})
                )

            else:
                await redis_manager.get_instance().publish(
                    channel=PubSubChannel.OUTGOING,
                    message=json.dumps({
                        "type": "MESSAGE",
                        "recipient_id": self.active_chat.sender,
                        "message": self.message
                    })
                )

            logger.debug(f"Published message to channel")

            with rx.session() as session:
                chat = session.get(Chat, self.active_chat.id)
                chat.last_active = datetime.now()

                if self.message.lower() == TERMINATION_COMMAND:
                    chat.status = RequestChatState.CLOSED

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
                chat = Chat(
                    sender=sender,
                    status=RequestChatState.NEW
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
                if chat.id == self.active_chat.id:
                    session.refresh(new_message)
                    self.current_chat_messages.insert(0, new_message)

    @rx.var(cache=False)
    def get_chats(self) -> List[Chat]:
        return [] if self.chats is None else self.chats

    @rx.var(cache=False)
    def get_messages(self) -> List[Message]:
        return self.current_chat_messages

    @rx.event(background=True)
    async def load_chats_subscribe_webhooks(self):
        logger.info(f"Bg, subscribe to pub/sub")
        async with self:
            self.load_initial_chats()

        async with redis_manager.get_instance().pubsub() as pubsub:
            logger.debug("[State] Listening to pub/sub..")

            while True:
                try:
                    await pubsub.psubscribe(PubSubChannel.CHANNEL)
                    logger.debug("Pub sub listener set up")

                    wh_msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)

                    logger.debug(f"[State] Received message: {wh_msg}")

                    if wh_msg is not None:
                        logger.debug(f"[State] WH pub/sub message: {wh_msg}")

                        async with self:
                            message = wh_msg.get("data").decode()

                            msg_data = json.loads(message)
                            logger.info(f"[State] Processing msg: {msg_data}")
                            self.receive_message(
                                msg_data.get("recipient_id"),
                                msg_data.get("message")
                            )

                except Exception as e:
                    logger.error(f"[State] Load redis chats unexpected error: {sys.exc_info()[0]}")

                await asyncio.sleep(2)
