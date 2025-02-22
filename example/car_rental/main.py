import os
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException

from pywce import Engine, client, EngineConfig, pywce_logger

load_dotenv()

app = FastAPI()

# create a .env and set the appropriate keys
wa_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
    app_secret=os.getenv("APP_SECRET"),
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

logger = pywce_logger(__name__)


async def task(payload: Dict, headers: Dict) -> None:
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)


# - API Endpoints -
@app.post("/chatbot/webhook")
@whatsapp.util.signature_required
async def handler(request: Request, background_tasks: BackgroundTasks) -> Response:
    """
        Handle incoming webhook events from WhatsApp and process them in the background.
    """
    payload_bytes = await request.body()
    payload = whatsapp.util.bytes_to_dict(payload_bytes)

    # Add processing task to background
    background_tasks.add_task(task, payload, dict(request.headers))

    # Immediately respond to WhatsApp with acknowledgment
    return Response(content="ACK", status_code=200)


@app.get("/chatbot/webhook")
async def verifier(request: Request) -> str:
    """Verify WhatsApp webhook callback URL challenge."""
    params = request.query_params
    mode, token, challenge = params.get("hub.mode"), params.get("hub.verify_token"), params.get("hub.challenge")

    if whatsapp.util.verify_webhook_verification_challenge(mode, token, challenge):
        return challenge
    raise HTTPException(status_code=403, detail="Forbidden")
