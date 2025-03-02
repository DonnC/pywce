from fastapi import APIRouter, Request, BackgroundTasks, HTTPException

from .config import whatsapp
from .tasks import engine_bg_task

router = APIRouter()

@router.post("/chatbot/webhook")
@whatsapp.util.signature_required
async def handler(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming webhook events from WhatsApp and process them in the background."""
    payload_bytes = await request.body()
    payload = whatsapp.util.bytes_to_dict(payload_bytes)

    # Add processing task to background
    background_tasks.add_task(engine_bg_task, payload, dict(request.headers))

    return "ack"


@router.get("/chatbot/webhook")
async def verifier(request: Request) -> str:
    """Verify WhatsApp webhook callback URL challenge."""
    params = request.query_params
    mode, token, challenge = params.get("hub.mode"), params.get("hub.verify_token"), params.get("hub.challenge")

    if whatsapp.util.webhook_challenge(mode, token, challenge):
        return challenge

    raise HTTPException(status_code=403, detail="Forbidden")
