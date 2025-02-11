"""
@author: DonnC
@project: pywce:chatbot
@file: main.py
@updated: 02-2025

This is an example standalone chatbot. Standalone in the sense that it uses pywce as
a WhatsApp Client Library only, without the engine template-driven superpower.
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Query

from pywce import client, pywce_logger

load_dotenv()

app = FastAPI()

logger = pywce_logger(__name__)

# create a .env and set the appropriate keys
config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN")
)
whatsapp = client.WhatsApp(config)


@app.post("/webhook")
async def handler(request: Request) -> Response:
    """
        Handle incoming webhook events from WhatsApp and process them
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

            # TODO: implement other types and process them accordingly
            match response.typ:
                case client.MessageTypeEnum.TEXT:
                    result = await whatsapp.send_message(
                        recipient_id=_user.wa_id,
                        message=f"You said: {response.body.get('body')}"
                    )

                case _:
                    result = await whatsapp.send_message(
                        recipient_id=_user.wa_id,
                        message=f"Received whatsapp message type as: {response.typ}"
                    )

            if whatsapp.util.was_request_successful(_user.wa_id, result):
                return Response(content="Ack", status_code=200)

    return Response(content="Something went wrong", status_code=400)


@app.get("/webhook")
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

    if result is None:
        return Response(content="Forbidden", status_code=403)

    return Response(content=result, status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
