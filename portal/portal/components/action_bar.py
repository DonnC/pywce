import reflex as rx

from ..state import SupportState
from ..style import input_style, button_style


def action_bar() -> rx.Component:
    return rx.hstack(
        rx.text_area(
            placeholder="Type a reply...",
            value=SupportState.message,
            on_change=SupportState.set_message,
            style=input_style,
            min_height="60px",
            max_height="200px",
            resize="vertical",
            width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon("send"),
                "Send",
            ),
            on_click=SupportState.send_message,
            style=button_style,
        ),
        width="100%",
        padding="4",
        spacing="4",
        # background="white",  # Optional: adds visual separation
        border_top="1px solid",
        border_color="gray.200",
    ),
