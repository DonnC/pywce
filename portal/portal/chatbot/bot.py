from typing import Dict

from fastapi import Request, Response, BackgroundTasks, Query, Depends

from pywce import Engine, pywce_logger
from pywce import client
from .dependencies import get_engine_instance, get_whatsapp_instance

logger = pywce_logger(__name__)


async def _webhook_event(payload: Dict, headers: Dict, engine: Engine) -> None:
    logger.debug("Portal: received webhook event, processing..")
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)


async def process_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        engine: Engine = Depends(get_engine_instance)
) -> Response:
    """
    Handle incoming webhook events from WhatsApp and process them in the background.

    delegates the incoming webhook event to pywce engine in the background for processing.
    """
    payload = await request.json()
    headers = dict(request.headers)

    # Add processing task to background
    background_tasks.add_task(_webhook_event, payload, headers, engine)

    # Immediately respond to WhatsApp with acknowledgment
    return Response(content="ACK", status_code=200)


async def verify_webhook(
        mode: str = Query(..., alias="hub.mode"),
        token: str = Query(..., alias="hub.verify_token"),
        challenge: str = Query(..., alias="hub.challenge"),
        whatsapp: client.WhatsApp = Depends(get_whatsapp_instance)
) -> Response:
    """
    Verify WhatsApp webhook callback url.
    """
    result = whatsapp.util.verify_webhook_verification_challenge(
        mode=mode, token=token, challenge=challenge
    )

    if result is None:
        return Response(content="Forbidden", status_code=403)

    return Response(content=result, status_code=200)
