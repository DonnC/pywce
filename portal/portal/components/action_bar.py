import reflex as rx

from ..state import ChatState
from ..style import input_style, button_style


def action_bar() -> rx.Component:
    return rx.hstack(
        rx.text_area(
            placeholder="Type a reply...\n\ntype /stop to terminate session",
            value=ChatState.message,
            on_change=ChatState.set_message,
            style=input_style,
            min_height="100px",
            max_height="400px",
            resize="vertical",
            width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon(
                    "send",
                    size=16
                ),
                "Send",
                align="center",
            ),
            on_click=ChatState.send_message,
            style=button_style,
        ),
        width="100%",
        class_name="px-4",
        spacing="4",
        align="center",
        border_color="gray.200",
    )
