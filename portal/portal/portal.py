from typing import List, Dict

import reflex as rx

# Temporary chat storage
chats: Dict[str, List[Dict[str, str]]] = {}  # Format: {user_phone_number: [{"sender": "user/admin", "message": "text"}]}


class SupportState(rx.State):
    user_phone: str = ""
    message: str = ""
    active_chat: str = ""  # Currently selected chat (user's phone number)

    def send_message(self):
        """Send a message to the user via WhatsApp API."""
        if self.user_phone and self.message:
            # Send whatsapp message
            # Save the message to the chat history
            if self.user_phone not in chats:
                chats[self.user_phone] = []
            chats[self.user_phone].append({"sender": "admin", "message": self.message})
            self.message = ""  # Clear the input field

    @rx.event
    def set_active_chat(self, phone_number: str):
        """Set the active chat to display."""
        self.active_chat = phone_number

    def receive_message(self, phone_number: str, message: str):
        """Simulate receiving a message from a user."""
        if phone_number not in chats:
            chats[phone_number] = []
        chats[phone_number].append({"sender": "user", "message": message})

    @rx.var
    def get_chats(self) -> List[str]:
        """Get a list of all active chats."""
        return list(chats.keys())

    @rx.var
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages for the active chat."""
        return chats.get(self.active_chat, [])


def chat_item(phone_number: str):
    """Render a chat item in the sidebar."""
    return rx.box(
        rx.button(
            phone_number,
            on_click=lambda: SupportState.set_active_chat(phone_number),
            width="100%",
            variant="ghost",
        ),
        padding="0.5em",
    )


def message_item(message: Dict[str, str]):
    """Render a single message in the chat."""
    return rx.box(
        rx.text(
            message.message,
            font_weight=rx.cond(message.sender == "admin", "bold", "normal"),  # Conditional styling
        ),
        text_align=rx.cond(message.sender == "admin", "right", "left"),  # Align text based on sender
        padding="0.5em",
    )


def index():
    return rx.vstack(
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
                rx.heading(f"Chat with {SupportState.active_chat}"),
                rx.foreach(SupportState.get_messages, message_item),
                rx.hstack(
                    rx.input(
                        placeholder="Type a message...",
                        value=SupportState.message,
                        on_change=SupportState.set_message,
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
