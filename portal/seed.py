"""
A script to add few conversation chats in the db
"""

from datetime import datetime, timedelta
from random import randint

import reflex as rx

from portal.constants import ChatRole, RequestChatState
from portal.model import Chat, Message


def seed_database():
    with rx.session() as session:
        chats = [
            Chat(sender="263778060126", status=RequestChatState.OPEN),
            Chat(sender="2637790123456", status=RequestChatState.CLOSED),
            Chat(sender="263770123456")
        ]

        # Add chats to session
        for chat in chats:
            session.add(chat)
        session.commit()

        conversations = [
            # Chat 1 conversation
            [
                (ChatRole.USER, "Hello, I need help with my order"),
                (ChatRole.ADMIN, "Hi there! I'd be happy to help. What's your order number?"),
                (ChatRole.USER, "It's ORDER123"),
                (ChatRole.ADMIN, "Let me check that for you")
            ],
            # Chat 2 conversation
            [
                (ChatRole.USER, "Is the support team available?"),
                (ChatRole.ADMIN, "Yes, how can we assist you today?"),
                (ChatRole.USER, "I have a technical question")
            ],
            # Chat 3 conversation
            [
                (ChatRole.USER, "Having issues with login"),
                (ChatRole.ADMIN, "I can help with that. What error are you seeing?"),
                (ChatRole.USER, "Invalid credentials error"),
                (ChatRole.ADMIN, "Let's reset your password")
            ]
        ]

        # Add messages with timestamps
        for chat, conversation in zip(chats, conversations):
            base_time = datetime.now() - timedelta(hours=randint(1, 5))

            for i, (sender, content) in enumerate(conversation):
                message = Message(
                    sender=sender,
                    content=content,
                    chat_id=chat.id,
                    timestamp=base_time + timedelta(minutes=i * randint(2, 5))
                )
                session.add(message)

        session.commit()


if __name__ == "__main__":
    print("[*] Seeding database...")
    seed_database()
    print("[*] Data seeded successfully")
