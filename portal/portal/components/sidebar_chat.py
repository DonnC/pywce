import reflex as rx

from ..model import Chat
from ..state import ChatState


def sidebar_chat(chat: Chat):
    return rx.hstack(
        rx.box(
            rx.badge(
                "",
                color_scheme=rx.cond(ChatState.active_chat.id == chat.id, "green", "gray"),
                variant="solid",
                size="2",
            ),
            padding_y="0.5em",
        ),
        rx.vstack(
            rx.text(
                chat.sender,
                color=rx.cond(ChatState.active_chat.id == chat.id, "white", "gray"),
                font_weight=rx.cond(ChatState.active_chat.id == chat.id, "bold", "normal"),
            ),
            rx.text(
                rx.moment(
                    chat.last_active,
                    from_now=True,
                    from_now_during=100000
                ),
                font_size="0.8em",
                color="gray",
                font_style="italic",
            ),
            align_items="start",
        ),
        width="100%",
        padding="1em",
        border_radius="md",
        border="1px solid",
        border_color=rx.cond(
            ChatState.active_chat.id == chat.id,
            "white",
            "gray"
        ),
        cursor="pointer",
        on_click=ChatState.set_active_chat(chat),
        spacing="3"
    )
