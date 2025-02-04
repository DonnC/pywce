from typing import Dict, List

from .constants import ChatRole
from .model import Message

# example chats db
chats: Dict[str, List[Message]] = {
    "+27123456789": [
        Message(sender=ChatRole.USER, content="Hi, I need help with my account."),
        Message(sender=ChatRole.ADMIN, content="Hello! How can I assist you today?")
    ],
    "+263712345678": [
        Message(sender=ChatRole.USER, content="I'm having issues with my claim."),
        Message(sender=ChatRole.ADMIN, content="I see. Could you please provide more details?")
    ]
}
