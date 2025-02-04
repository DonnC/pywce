from datetime import datetime
from typing import List, Optional

import reflex as rx
from sqlmodel import Field, Relationship

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
                    1   - requesting live support
                    0   - acquired communication link
                   -1   - no agent available
        :var last_active: last interaction message received
        :var messages: conversation messages with admin / agent

    """
    sender: str
    status: int = -1
    last_active: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = Relationship(back_populates="chat")
