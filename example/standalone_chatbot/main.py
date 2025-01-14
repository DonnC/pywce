import uvicorn
from fastapi import FastAPI, Request, Response, Query, Depends

import pywce
from example.standalone_chatbot.dependencies import get_whatsapp_instance
from pywce.engine_logger import get_engine_logger

logger = get_engine_logger(__name__)

# - App Metadata -
app = FastAPI(
    name="Pywce WhatsApp ChatBot",
    description="An example chatbot using pywce standalone whatsapp module",
    version="0.0.1",
    contact={
        "name": "DonnC",
        "email": "donnclab@gmail.com",
    },
    license_info={"name": "MIT"},
)


# - API Endpoints -
@app.post("/webhook")
async def process_webhook(
        request: Request,
        whatsapp: pywce.WhatsApp = Depends(get_whatsapp_instance)
) -> Response:
    """
    Handle incoming webhook events from WhatsApp and process them
    :param request: FastAPI Request object containing the webhook payload
    :param whatsapp: WhatsApp instance to process webhook challenge
    :return: HTTP Response with "ACK" content
    """
    payload = await request.json()
    headers = dict(request.headers)

    if whatsapp.util.verify_webhook_payload(payload, headers):
        if whatsapp.util.is_valid_webhook_message(payload):
            # simplify getting whatsapp user object with waId, msgId, timestamp and name
            _user = whatsapp.util.get_wa_user(payload)
            logger.info(f"Current whatsapp user: {_user}")

            # simplify webhook message type and data
            response = whatsapp.util.get_response_structure(payload)
            logger.info(f"Webhook response structure: {response}")

            match response.typ:
                case pywce.MessageTypeEnum.TEXT:
                    result = whatsapp.send_message(
                        recipient_id=_user.wa_id,
                        message=f"You said: {response.body.get('body')}"
                    )

                # TODO: implement other types and process them accordingly

                case _:
                    result = whatsapp.send_message(
                        recipient_id=_user.wa_id,
                        message=f"Received whatsapp message type as: {response.typ}"
                    )

            if whatsapp.util.was_request_successful(_user.wa_id, result):
                return Response(content="Ack", status_code=200)

    return Response(content="Something went wrong", status_code=400)


@app.get("/webhook")
async def verify_webhook(
        mode: str = Query(...),
        token: str = Query(...),
        challenge: str = Query(...),
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
