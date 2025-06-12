import logging

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Response, status

from pywce import FlowEndpointException
from .config import whatsapp
from .tasks import engine_bg_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
def index():
    return {
        "status": "success",
        "message": "Welcome to the [pywce] WCE API!",
        "github": "https://github.com/DonnC/pywce"
    }


@router.post("/chatbot/webhook")
async def handle_incoming_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_bytes = await request.body()
    payload = whatsapp.util.bytes_to_dict(payload_bytes)

    # Add processing task to background: recommended approach
    background_tasks.add_task(engine_bg_task, payload, dict(request.headers))

    return "ack"


@router.get("/chatbot/webhook")
def verify_webhook_challenge(request: Request) -> Response:
    params = request.query_params
    mode, token, challenge = params.get("hub.mode"), params.get("hub.verify_token"), params.get("hub.challenge")

    if whatsapp.util.webhook_challenge(mode, challenge, token):
        return Response(content=challenge, status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/chatbot/flow")
async def handle_flow_endpoint_request(request: Request):
    try:
        json_data = await request.json()
        flow_response = whatsapp.util.flow_endpoint_handler(json_data)

        return Response(content=flow_response, media_type='text/plain', status_code=status.HTTP_200_OK)

    except FlowEndpointException as e:
        logger.error("Flow endpoint error: %s", e, exc_info=True)
        return Response(content=e.message, status_code=int(e.data))

    except Exception as e:
        logger.error("Failed to handle flow request: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error occurred: {e}")
