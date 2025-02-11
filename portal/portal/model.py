from datetime import datetime
from typing import List, Optional

import reflex as rx
from sqlmodel import Field, Relationship

from .constants import RequestChatState


class Message(rx.Model, table=True):
    content: str
    sender: str
    timestamp: datetime = Field(default_factory=datetime.now)
    chat_id: int = Field(foreign_key="chat.id")
    chat: Optional["Chat"] = Relationship(back_populates="messages")


class Chat(rx.Model, table=True):
    """
        Main chat model, each user will have a chat entry with conversation messages

        :var sender: client phone number > wa_id
        :var status: show chat state
        :var last_active: last interaction message received
        :var messages: conversation messages with admin / agent

    """
    sender: str
    status: str = RequestChatState.NEW
    last_active: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = Relationship(back_populates="chat")
