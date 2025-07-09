import logging

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Response, status

from pywce import FlowEndpointException
from .config import whatsapp
from .global_hooks import flow_endpoint_handler
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
        enc_json_data = await request.json()

        flow_response = whatsapp.util.flow_endpoint_handler(
            encrypted_flow_payload=enc_json_data,
            handler=flow_endpoint_handler
        )

        return Response(content=flow_response, media_type='text/plain', status_code=status.HTTP_200_OK)

    except FlowEndpointException as e:
        logger.error("Flow endpoint error: %s", e, exc_info=True)
        return Response(content=e.message, status_code=int(e.data))

    except Exception as e:
        logger.error("Failed to handle flow request: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error occurred: {e}")


@router.post("/chatbot/manual-flow")
async def handle_flow_endpoint_request_manually(request: Request):
    """
        Manually process a flow endpoint request
    """

    try:
        # 1. get request encrypted flow request
        enc_json_data = await request.json()

        # 2. get decrypted flow payload
        dec_flow_response = whatsapp.util.get_flow_payload(enc_json_data)

        # 3. handle business logic
        result: dict = flow_endpoint_handler(dec_flow_response.payload)

        # . 4 generate flow encrypted response as str
        flow_response = whatsapp.util.generate_flow_response_payload(result, dec_flow_response)

        # 5. Return a text plain response
        return Response(content=flow_response, media_type='text/plain', status_code=status.HTTP_200_OK)

    except FlowEndpointException as e:
        logger.error("Flow endpoint error: %s", e, exc_info=True)
        return Response(content=e.message, status_code=int(e.data))

    except Exception as e:
        logger.error("Failed to handle flow request: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error occurred: {e}")
