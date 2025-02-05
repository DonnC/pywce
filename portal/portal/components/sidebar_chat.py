import reflex as rx

from .chat_badge import chat_badge
from ..model import Chat
from ..state import SupportState


def sidebar_chat(chat: Chat):
    return rx.box(
        rx.vstack(
            rx.text(
                chat.sender,
                color=rx.cond(SupportState.active_chat.id == chat.id, "white", "gray"),
                font_weight=rx.cond(SupportState.active_chat.id == chat.id, "bold", "normal"),
            ),
            rx.cond(
                chat.id != SupportState.active_chat.id,
                rx.text(
                    rx.moment(
                        chat.last_active,
                        from_now=True,
                        from_now_during=100000
                    ),
                    font_style="italic",
                    color="gray",
                    font_size="0.8em",
                ),
            ),
            chat_badge(chat.status),
            align_items="start",
            width="100%",
        ),
        padding="1em",
        cursor="pointer",
        background_color=rx.cond(
            chat.id == SupportState.active_chat,
            "rgb(59, 130, 246)",
            "transparent"
        ),
        border_radius="md",
        on_click=lambda: SupportState.set_active_chat(chat),
    )
