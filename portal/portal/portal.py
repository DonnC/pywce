from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict

import reflex as rx

from .style import Style


# ----------------------------
# Define a Message model to represent chat messages
# ----------------------------
@dataclass
class Message:
    sender: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __str__(self):
        return f"[{self.timestamp}] {self.sender}: {self.content}"


# ----------------------------
# Temporary chat storage using a per-user chat history model
# Format: {user_phone_number: List[Message]}
# ----------------------------
chats: Dict[str, List[Message]] = {
    "+27123456789": [
        Message(sender="user", content="Hi, I need help with my account."),
        Message(sender="admin", content="Hello! How can I assist you today?")
    ],
    "+263712345678": [
        Message(sender="user", content="I'm having issues with my claim."),
        Message(sender="admin", content="I see. Could you please provide more details?")
    ]
}


class SupportState(rx.State):
    message: str = ""
    active_chat: str = "+263712345678"  # Currently selected chat (user's phone number)

    @rx.event
    def set_admin_message(self, new_message: str):
        print(f"New incoming message: {new_message}")
        self.message = new_message
        yield
        print("New set message: ", self.message)

    @rx.event
    def send_message(self):
        print(f"Received new message to send: {self.message}")

        # TODO: Send a message to the user via WhatsApp API
        if self.active_chat and self.message:
            new_message = Message(sender="admin", content=self.message.strip())

            print(f"Sending new message: {new_message}")

            # Save the message to the chat history
            if self.active_chat not in chats:
                chats[self.active_chat] = []
            chats[self.active_chat].append(new_message)
            self.message = ""

            print("Active chat messages: ", chats[self.active_chat])
            print("New reset message: ", self.message)
            yield

    @rx.event
    def set_current_active_chat(self, phone_number: str):
        """Set the active chat to display."""
        print(f"Setting active chat to {phone_number}")
        self.active_chat = phone_number
        print("Current active chat: ", self.active_chat)
        yield

    def receive_message(self, phone_number: str, message: str):
        """TODO: Simulate receiving a message from a user."""
        new_message = Message(sender="user", content=message.strip())

        if phone_number not in chats:
            chats[phone_number] = []

        chats[phone_number].append(new_message)

    @rx.var
    def get_chats(self) -> List[str]:
        """Get a list of all active chats."""
        return list(chats.keys())

    @rx.var
    def get_messages(self) -> List[Message]:
        """Get messages for the active chat."""
        return chats.get(self.active_chat, [])


def chat_item(phone_number: str):
    """Render a chat item in the sidebar."""
    return rx.box(
        rx.button(
            phone_number,
            on_click=SupportState.set_current_active_chat(phone_number),
            width="100%",
            variant="ghost",
        ),
        padding="0.5em",
    )


# def chat_item(chat: str) -> rx.Component:
#     return rx.box(
#         rx.vstack(
#             rx.text(
#                 chat,
#                 color="white" if chat == SupportState.active_chat else "black",
#                 font_weight="bold" if chat == SupportState.active_chat else "normal",
#             ),
#             rx.cond(
#                 chat != SupportState.active_chat,
#                 rx.text(
#                     "Last active 2h ago",  # Replace with actual timestamp
#                     font_style="italic",
#                     color="gray",
#                     font_size="0.8em",
#                 ),
#             ),
#             align_items="start",
#             width="100%",
#         ),
#         padding="1em",
#         cursor="pointer",
#         background_color=rx.cond(
#             chat == SupportState.active_chat,
#             "rgb(59, 130, 246)",  # Blue when active
#             "transparent"
#         ),
#         border_radius="md",
#         on_click=lambda: SupportState.set_active_chat(chat),
#     )
#
# # In your State class
# class SupportState(rx.State):
#     active_chat: str = ""
#     last_active: Dict[str, datetime] = {}  # Store last active times
#
#     @rx.event
#     def set_active_chat(self, chat: str):
#         self.active_chat = chat


def message_item(message: Message) -> rx.Component:
    return rx.box(
        rx.text(
            message.content,
            style=rx.cond(message.sender == "admin", Style.admin, Style.user),
        ),
        text_align=rx.cond(message.sender == "admin", "right", "left"),
        width="100%",
    )


def index():
    return rx.vstack(
        rx.heading(f"Active Chat: {SupportState.active_chat} | Message: {SupportState.message}"),
        rx.hstack(
            # Sidebar with active chats
            rx.vstack(
                rx.heading("Active Chats"),
                rx.foreach(SupportState.get_chats, chat_item),
                width="20%",
                border_right="1px solid #ddd",
                padding="1em",
            ),
            # Main chat window
            rx.vstack(
                rx.heading(rx.cond(SupportState.active_chat, f"Chat with {SupportState.active_chat}", "Select a Chat")),
                rx.box(
                    rx.foreach(SupportState.get_messages, message_item),
                    padding="1em",
                    height="70vh",
                    overflow_y="auto",  # Enable scrolling
                ),
                rx.hstack(
                    rx.input(
                        placeholder="type a message...",
                        value=SupportState.message,
                        on_change=SupportState.set_admin_message,
                        width="80%",
                    ),
                    rx.button("Send", on_click=SupportState.send_message),
                ),
                width="80%",
                padding="1em",
            ),
            width="100%",
            height="100vh",
        ),
    )


# Create the app
app = rx.App()
app.add_page(index)
