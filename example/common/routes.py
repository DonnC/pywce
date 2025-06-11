import logging

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Response
from starlette.responses import PlainTextResponse

from pywce import FlowEndpointException
from .config import whatsapp
from .tasks import engine_bg_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
def index(request: Request):
    return {
        "status": "success",
        "message": "Welcome to the [pywce] WCE API!",
        "github": "https://github.com/DonnC/pywce"
    }


@router.post("/chatbot/webhook")
async def handler(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming webhook events from WhatsApp and process them in the background."""
    payload_bytes = await request.body()
    payload = whatsapp.util.bytes_to_dict(payload_bytes)

    # Add processing task to background: recommended approach
    background_tasks.add_task(engine_bg_task, payload, dict(request.headers))

    return "ack"


@router.get("/chatbot/webhook")
def verifier(request: Request) -> Response:
    """Verify WhatsApp webhook callback URL challenge."""
    params = request.query_params
    mode, token, challenge = params.get("hub.mode"), params.get("hub.verify_token"), params.get("hub.challenge")

    if whatsapp.util.webhook_challenge(mode, challenge, token):
        return Response(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Forbidden")


# For flow endpoint
@router.post("/chatbot/flow")
async def handle_flow_request(request: Request):
    """
        Response(content=encrypted_response, media_type="application/octet-stream")
    """
    try:
        json_data = await request.json()

        flow_response = whatsapp.util.flow_endpoint_handler(json_data)

        return PlainTextResponse(flow_response, media_type='text/plain')

    except FlowEndpointException as e:
        logger.error("Flow endpoint error: %s", e, exc_info=True)
        raise HTTPException(status_code=int(e.data), detail=e.message)

    except Exception as e:
        logger.error("Failed to handle flow request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
