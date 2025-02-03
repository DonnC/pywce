import reflex as rx

from .action_bar import action_bar
from .message_card import message_card
from ..state import SupportState


def chat_window() -> rx.Component:
    return rx.vstack(
        rx.heading(
            rx.cond(
                SupportState.active_chat,
                f"Chat with {SupportState.active_chat}",
                "Select a Chat"
            )
        ),
        rx.box(
            rx.foreach(
                SupportState.get_messages,
                message_card
            ),
            padding="1em",
            height="70vh",
            overflow_y="auto",
        ),
        rx.spacer(),
        action_bar(),
        spacing="4",
        height="100%",
        align="stretch",
    )
