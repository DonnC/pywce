from typing import Dict

from fastapi import FastAPI, Request, Response, BackgroundTasks, Query

import pywce
from pywce.engine_logger import get_engine_logger

app = FastAPI(
    name="Pywce Bot",
    description="An example chatbot using pywce engine",
    version="0.0.1",
    author="DonnC",
    email="donnclab@gmail.com",
    license="MIT"
)

# - define configs & dependencies -
logger = get_engine_logger(__name__)
session_manager = pywce.DefaultSessionManager()

start_menu = "START-MENU"

wa_config = pywce.WhatsAppConfig(
    token="TOKEN",
    phone_number_id="PHONE_NUMBER_ID",
    hub_verification_token="HUB_VERIFICATION_TOKEN",
    use_emulator=True
)

whatsapp = pywce.WhatsApp(whatsapp_config=wa_config)

config = pywce.PywceEngineConfig(
    whatsapp=whatsapp,
    templates_dir="templates",
    trigger_dir="triggers",
    start_template_stage=start_menu,
    session_manager=session_manager
)

engine = pywce.PywceEngine(config=config)


# - end -

async def webhook_event(payload: Dict, headers: Dict) -> None:
    """
    Initiates engine processing, process webhook payload via pywce engine

    :param payload: WhatsApp webhook payload
    :param headers: WhatsApp webhook headers
    :return: None
    """
    logger.info("Received webhook event, processing..")
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)
    logger.info("Webhook event processed.")


@app.post("/webhook")
async def process_webhook(request: Request, background_tasks: BackgroundTasks):
    # Extract webhook payload and headers
    payload = await request.json()
    headers = dict(request.headers)

    # Publish the event in the background for engine to process
    background_tasks.add_task(webhook_event, payload, headers)

    # Immediately respond with an acknowledgment to avoid receiving same webhook response
    return Response(content="ACK", status_code=200)


@app.get("/webhook")
async def verify_webhook(mode: str = Query(str), token: str = Query(str), challenge: str = Query(str)):
    """
    Verify WhatsApp webhook by checking query parameters.
    """
    result = whatsapp.util.verify_webhook_verification_challenge(mode=mode, token=token, challenge=challenge)

    if result is None:
        return Response(content="Forbidden", status_code=403)

    return Response(content=result, status_code=200)
