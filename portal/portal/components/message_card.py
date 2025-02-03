import reflex as rx

from ..constants import ChatRole
from ..model import Message
from ..style import admin_style, user_style

# FIXME: a long way but this is a common issue in reflex
#        can't do conditional style rendering: https://github.com/reflex-dev/reflex/issues/2979


# TODO: format time using moments

def _admin_message(message: Message) -> rx.Component:
    return rx.box(
        rx.box(
            rx.vstack(
                rx.text(message.content, style=admin_style),
                rx.text(
                    message.timestamp,
                    font_size="xs",
                    color="gray.500",
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
                    message.timestamp,
                    font_size="xs",
                    color="gray.500",
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
