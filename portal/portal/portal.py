import asyncio
import json
from contextlib import asynccontextmanager

import reflex as rx

from pywce import pywce_logger
from .chatbot.bot import ep_process_webhook, ep_verify_webhook, engine
from .components.chat_window import chat_window
from .components.footer import footer
from .components.sidebar import sidebar
from .constants import PubSubChannel, TERMINATION_COMMAND
from .redis_manager import RedisManager
from .state import ChatState

logger = pywce_logger(__name__, False)


@asynccontextmanager
async def setup_redis():
    logger.debug("Setting up UI pub/sub listener..")

    redis_manager = RedisManager()
    r = redis_manager.get_instance()

    async def listen_to_channel():
        async with r.pubsub() as pubsub:
            while True:
                try:
                    await pubsub.psubscribe(PubSubChannel.OUTGOING)

                    wh_msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)

                    if wh_msg is not None:
                        message = wh_msg["data"].decode()
                        msg_data = json.loads(message)
                        logger.info(f"New outgoing Agent msg: {msg_data}")

                        if msg_data.get('type', 'MESSAGE')  == TERMINATION_COMMAND:
                            engine.terminate_external_handler(recipient_id=msg_data['recipient_id'])

                        else:
                            await engine.ext_handler_respond(recipient_id=msg_data['recipient_id'], message=msg_data['message'])

                except:
                    logger.error(f"Agent message listener unexpected error", exc_info=True)

                await asyncio.sleep(0.3)

    task = asyncio.create_task(listen_to_channel())

    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.debug("Task cancelled")


@rx.page(on_load=ChatState.load_chats_subscribe_webhooks)
def index() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "PYWCE LiveSupport",
            class_name="p-4"
        ),
        rx.cond(
            ChatState.is_loading,
            rx.center(rx.spinner()),
            rx.hstack(
                sidebar(),
                rx.box(
                    rx.cond(
                        ChatState.active_chat == None,
                        rx.vstack(
                            rx.icon(
                                "inbox",  # lucide icon
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

app.register_lifespan_task(setup_redis)

app.api.add_api_route("/chatbot/webhook", ep_process_webhook, methods=["POST"])
app.api.add_api_route("/chatbot/webhook", ep_verify_webhook, methods=["GET"])

app.add_page(index)
