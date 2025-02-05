import reflex as rx

from ..constants import ChatRole
from ..model import Message
from ..style import admin_style, user_style


#  https://github.com/reflex-dev/reflex/issues/2979
def _admin_message(message: Message) -> rx.Component:
    return rx.box(
        rx.box(
            rx.vstack(
                rx.text(message.content, style=admin_style),
                rx.text(
                    rx.moment(
                        message.timestamp,
                        from_now=True,
                        from_now_during=100000
                    ),
                    font_style="italic",
                    font_size="xs",
                    color="gray",
                    align_self="flex-end",
                ),
                align_items="flex-end",
                spacing="1",
            ),
            text_align="right",
        ),
        margin_y="1em",
        width="100%"
    )


def _user_message(message: Message) -> rx.Component:
    return rx.box(
        rx.box(
            rx.vstack(
                rx.text(message.content, style=user_style),
                rx.text(
                    rx.moment(
                        message.timestamp,
                        from_now=True,
                        from_now_during=100000
                    ),
                    font_style="italic",
                    font_size="xs",
                    color="gray",
                    align_self="flex-start",
                ),
                align_items="flex-start",
                spacing="1",
            ),
            text_align="left",
        ),
        margin_y="1em",
        width="100%"
    )


def message_card(message: Message) -> rx.Component:
    return rx.cond(message.sender == ChatRole.ADMIN, _admin_message(message), _user_message(message))
