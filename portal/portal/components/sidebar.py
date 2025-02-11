import reflex as rx

from .sidebar_chat import sidebar_chat
from ..state import ChatState


def sidebar() -> rx.Component:
    return rx.vstack(
        rx.heading("Active Chats", size="4", padding="1em"),
        rx.divider(),
        rx.foreach(ChatState.get_chats, sidebar_chat),
        align_items="stretch",
        overflow_y="auto",
        height="100vh",
        padding="1em",
        width="20%",
        border_right="1px solid #ddd",
        border_color="gray.200",
    )
