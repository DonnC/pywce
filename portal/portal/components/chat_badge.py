import reflex as rx


def chat_badge(chat_state: int=-1) -> rx.Component:
    return rx.badge(
        rx.match(
            chat_state,
            (-1, "New"),
            (0, "Live"),
            (1, "NA"),
            "gray"
        ),
        color_scheme=rx.match(
            chat_state,
            (-1, "red"),
            (0, "blue"),
            (1, "orange"),
            "gray"
        )
    )
