import reflex as rx

from .chatbot.bot import verify_webhook, process_webhook
from .components.chat_window import chat_window
from .components.footer import footer
from .components.sidebar import sidebar
from .state import SupportState


@rx.page(on_load=SupportState.load_initial_chats)
def index() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "PYWCE LiveSupport",
            class_name="p-4"
        ),
        rx.cond(
            SupportState.is_loading,
            rx.center(rx.spinner()),
            rx.hstack(
                sidebar(),
                rx.box(
                    rx.cond(
                        SupportState.active_chat == None,
                        rx.vstack(
                            rx.icon(
                                "inbox", # lucide icon
                                size=48,
                                color=rx.color("gray", 4)
                            ),
                            rx.heading("No Chat Selected", size="4", color="gray"),
                            rx.text("Select a chat to begin messaging", color="gray"),
                            align="center",
                            justify="center",
                            height="100%",
                            spacing="4",
                            padding="8",
                        ),
                        chat_window(),
                    ),
                    flex="1",
                    height="90vh"
                ),
                width="100%",
                height="90vh",
            )
        ),
        footer()
    )


app = rx.App()
app.api.add_api_route("/chatbot/webhook", process_webhook, methods=["POST"])
app.api.add_api_route("/chatbot/webhook", verify_webhook, methods=["GET"])
app.add_page(index)
