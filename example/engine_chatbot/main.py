from typing import Dict

import uvicorn
from fastapi import FastAPI, Request, Response, BackgroundTasks, Query, Depends

import pywce
from example.engine_chatbot.dependencies import get_engine_instance, get_whatsapp_instance
from pywce.engine_logger import get_engine_logger

logger = get_engine_logger(__name__)

# - App Metadata -
app = FastAPI(
    name="Pywce Bot",
    description="An example chatbot using pywce core engine",
    version="0.0.1",
    contact={
        "name": "DonnC",
        "email": "donnclab@gmail.com",
    },
    license_info={"name": "MIT"},
)


# - Utility Functions -
async def webhook_event(payload: Dict, headers: Dict, engine: pywce.PywceEngine) -> None:
    """
    Process webhook event in the background using pywce engine.

    :param engine: Pywce engine instance
    :param payload: WhatsApp webhook payload
    :param headers: WhatsApp webhook headers
    """
    logger.debug("Received webhook event, processing..")
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)


# - API Endpoints -
@app.post("/chatbot/webhook")
async def process_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        engine: pywce.PywceEngine = Depends(get_engine_instance)
) -> Response:
    """
    Handle incoming webhook events from WhatsApp and process them in the background.

    :param request: FastAPI Request object containing the webhook payload
    :param background_tasks: FastAPI BackgroundTasks object for async processing
    :param engine: pywce.PywceEngine instance for webhook processing
    :return: HTTP Response with "ACK" content
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
        whatsapp: pywce.WhatsApp = Depends(get_whatsapp_instance)
) -> Response:
    """
    Verify WhatsApp webhook using query parameters.

    :param whatsapp: WhatsApp instance to process webhook challenge
    :return: HTTP Response with challenge content if verification succeeds, otherwise "Forbidden"
    """
    result = whatsapp.util.verify_webhook_verification_challenge(
        mode=mode, token=token, challenge=challenge
    )

    if result is None:
        return Response(content="Forbidden", status_code=403)

    return Response(content=result, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
