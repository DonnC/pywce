import asyncio
import json
from contextlib import asynccontextmanager

import reflex as rx
from fastapi import BackgroundTasks

from pywce import pywce_logger
from .chatbot.bot import ep_process_webhook, ep_verify_webhook
from .components.chat_window import chat_window
from .components.footer import footer
from .components.sidebar import sidebar
from .constants import PubSubChannel
from .redis_manager import RedisManager
from .state import ChatState

logger = pywce_logger(__name__)
background_tasks = BackgroundTasks()


@asynccontextmanager
async def setup_redis():
    logger.debug("[Portal] Setting up pub/sub listener..")

    redis_manager = RedisManager()
    r = redis_manager.get_instance()

    async def listen_to_channel():
        async with r.pubsub() as pubsub:
            while True:
                try:
                    await pubsub.psubscribe(PubSubChannel.CHANNEL)
                    logger.debug("[Portal] Pub sub listener set up")

                    wh_msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)

                    logger.debug(f"[Portal] Got message: {wh_msg}")

                    if wh_msg is not None:
                        logger.debug(f"[Portal] WH pub/sub message: {wh_msg}")

                        channel = wh_msg["channel"].decode()
                        message = wh_msg["data"].decode()

                        if channel == PubSubChannel.OUTGOING:
                            msg_data = json.loads(message)
                            logger.info(f"[Portal] Received agent msg: {msg_data}")
                            # TODO: sent msg to channel

                except Exception as e:
                    logger.error(f"[Portal] Listen channel unexpected error", exc_info=True)

                await asyncio.sleep(3)

    background_tasks.add_task(listen_to_channel)

    await background_tasks()
    yield


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
app.api.add_api_route("/chatbot/webhook", ep_process_webhook, methods=["POST"])
app.api.add_api_route("/chatbot/webhook", ep_verify_webhook, methods=["GET"])
app.add_page(index)
app.register_lifespan_task(setup_redis)
