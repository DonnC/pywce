import reflex as rx

from ..state import SupportState

def sidebar_chat(chat: str):
    return rx.box(
        rx.vstack(
            rx.text(
                chat,
                color=rx.cond(SupportState.active_chat == chat, "white", "gray"),
                font_weight=rx.cond(SupportState.active_chat == chat, "bold", "normal"),
            ),
            rx.cond(
                chat != SupportState.active_chat,
                rx.text(
                    "Last active 2h ago",  # TODO: Replace with actual timestamp
                    font_style="italic",
                    color="gray",
                    font_size="0.8em",
                ),
            ),
            align_items="start",
            width="100%",
        ),
        padding="1em",
        cursor="pointer",
        background_color=rx.cond(
            chat == SupportState.active_chat,
            "rgb(59, 130, 246)",
            "transparent"
        ),
        border_radius="md",
        on_click=lambda: SupportState.set_active_chat(chat),
    )
