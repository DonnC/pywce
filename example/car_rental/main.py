import os
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, BackgroundTasks, Query

from pywce import Engine, client, EngineConfig

load_dotenv()

app = FastAPI()

# create a .env and set the appropriate keys
wa_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
    use_emulator=int(os.getenv("USE_EMULATOR", 0)) == 1
)

whatsapp = client.WhatsApp(wa_config)

eng_config = EngineConfig(
    whatsapp=whatsapp,
    templates_dir=os.getenv("TEMPLATES_DIR"),
    trigger_dir=os.getenv("TRIGGERS_DIR"),
    start_template_stage=os.getenv("START_STAGE")
)

engine = Engine(config=eng_config)


async def task(payload: Dict, headers: Dict) -> None:
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)


# - API Endpoints -
@app.post("/chatbot/webhook")
async def handler(request: Request, background_tasks: BackgroundTasks) -> Response:
    """
        Handle incoming webhook events from WhatsApp and process them in the background.
    """
    payload = await request.json()

    # Add processing task to background
    background_tasks.add_task(task, payload, dict(request.headers))

    # Immediately respond to WhatsApp with acknowledgment
    return Response(content="ACK", status_code=200)


@app.get("/chatbot/webhook")
async def verifier(
        mode: str = Query(..., alias="hub.mode"),
        token: str = Query(..., alias="hub.verify_token"),
        challenge: str = Query(..., alias="hub.challenge")
) -> Response:
    """
        Verify WhatsApp webhook callback url challenge.
    """
    result = whatsapp.util.verify_webhook_verification_challenge(
        mode=mode, token=token, challenge=challenge
    )

    return Response(content="Forbidden", status_code=403) if result is None \
        else Response(content=result, status_code=200)
