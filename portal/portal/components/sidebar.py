import reflex as rx

from .sidebar_chat import sidebar_chat
from ..state import SupportState


def sidebar() -> rx.Component:
    return rx.vstack(
        rx.heading("Active Chats"),
        rx.foreach(SupportState.get_chats, sidebar_chat),
        width="20%",
        border_right="1px solid #ddd",
        padding="1em",
    )
