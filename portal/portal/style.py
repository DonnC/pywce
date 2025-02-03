import reflex as rx

# Common styles for user and admin.
shadow = "rgba(0, 0, 0, 0.15) 0px 2px 8px"
chat_margin = "20%"
message_style = dict(
    padding="1em",
    border_radius="5px",
    margin_y="0.5em",
    box_shadow=shadow,
    max_width="30em",
    display="inline-block",
)

# Set specific styles for user and admin.
admin_style = message_style | dict(
    margin_left=chat_margin,
    background_color=rx.color("gray", 4),
)
user_style = message_style | dict(
    margin_right=chat_margin,
    background_color=rx.color("accent", 8),
)

# Styles for the action bar.
input_style = dict(
    border_width="1px",
    padding="0.5em",
    box_shadow=shadow,
    width="350px",
)

button_style = dict(
    background_color=rx.color("accent", 10),
    box_shadow=shadow,
)
