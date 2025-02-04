import reflex as rx

from ..model import Chat
from ..state import SupportState


def sidebar_chat(chat: Chat):
    print("Current chat: ", chat)

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
                    chat.last_active,
                    font_style="italic",
                    color="gray",
                    font_size="0.8em",
                ),
            ),
            rx.text(chat),
            rx.badge(chat.sender),
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
