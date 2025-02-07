from typing import Dict

import uvicorn
from fastapi import FastAPI, Request, Response, BackgroundTasks, Query, Depends

from example.engine_chatbot.dependencies import get_engine_instance, get_whatsapp_instance
from pywce import Engine, pywce_logger, client

logger = pywce_logger(__name__)

app = FastAPI()


# - Utility Function -
async def webhook_event(payload: Dict, headers: Dict, engine: Engine) -> None:
    """
    Process webhook in the background using pywce engine.
    """
    logger.debug("Received webhook event, processing..")
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)


# - API Endpoints -
@app.post("/chatbot/webhook")
async def process_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        engine: Engine = Depends(get_engine_instance)
) -> Response:
    """
    Handle incoming webhook events from WhatsApp and process them in the background.
    """
    payload = await request.json()
    headers = dict(request.headers)

    # Add processing task to background
    background_tasks.add_task(webhook_event, payload, headers, engine)

    # Immediately respond to WhatsApp with acknowledgment
    return Response(content="ACK", status_code=200)


@app.get("/chatbot/webhook")
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
