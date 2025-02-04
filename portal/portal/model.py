from datetime import datetime
from typing import List, Optional

import reflex as rx
from sqlmodel import Field, Relationship


# @dataclass
# class Message:
#     sender: str
#     content: str
#     timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#
#     def __str__(self):
#         return f"[{self.timestamp}] {self.sender}: {self.content}"
#
# @dataclass
# class Chat:
#     sender: str
#     messages: List[Message] = field(default_factory=list)
#
#     def __str__(self):
#         return f"[{self.sender}] {self.messages}"


class Message(rx.Model, table=True):
    content: str
    sender: str
    timestamp: datetime = Field(default_factory=datetime.now)
    chat_id: int = Field(foreign_key="chat.id")
    chat: Optional["Chat"] = Relationship(
        back_populates="messages",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


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
