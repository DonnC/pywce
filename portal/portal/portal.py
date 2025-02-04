import reflex as rx

from .chatbot.bot import verify_webhook, process_webhook
from .components.chat_window import chat_window
from .components.footer import footer
from .components.sidebar import sidebar

def index() -> rx.Component:
    return rx.vstack(
        rx.heading("Live Support"),
        rx.hstack(
            sidebar(),
            rx.box(
                chat_window(),
                flex="1",
                height="95vh"
            ),
            width="100%",
            height="95vh",
        ),
        footer()
    )

app = rx.App()
app.api.add_api_route("/chatbot/webhook", process_webhook, methods=["POST"])
app.api.add_api_route("/chatbot/webhook", verify_webhook, methods=["GET"])
app.add_page(index)
