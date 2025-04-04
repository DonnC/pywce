"""
@author: DonnC
@project: pywce:chatbot
@file: main.py
@updated: 02-2025

This is an example standalone chatbot. Standalone in the sense that it uses pywce as
a WhatsApp Client Library only, without the engine templates-driven superpower.
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException

from pywce import client

load_dotenv()

app = FastAPI()

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
    payload_bytes = await request.body()
    payload = whatsapp.util.bytes_to_dict(payload_bytes)

    if whatsapp.util.is_valid_webhook_message(payload):
        # simplify getting whatsapp user object with waId, msgId, timestamp and name
        _user = whatsapp.util.get_wa_user(payload)
        print(f"Current whatsapp user: {_user}")

        # simplify webhook message type and data
        response = whatsapp.util.get_response_structure(payload)
        print(f"Webhook response structure: {response}")

        # TODO: implement other types and process them accordingly
        match response.typ:
            case client.MessageTypeEnum.TEXT:
                result = whatsapp.send_message(
                    recipient_id=_user.wa_id,
                    message=f"You said: {response.body.get('body')}"
                )

            case _:
                result = whatsapp.send_message(
                    recipient_id=_user.wa_id,
                    message=f"Received whatsapp message type as: {response.typ}"
                )

        if whatsapp.util.was_request_successful(_user.wa_id, result):
            return Response(content="Ack", status_code=200)

    return Response(content="Something went wrong", status_code=400)


@app.get("/chatbot/webhook")
async def verifier(request: Request) -> str:
    """Verify WhatsApp webhook callback URL challenge."""
    params = request.query_params
    mode, token, challenge = params.get("hub.mode"), params.get("hub.verify_token"), params.get("hub.challenge")

    if whatsapp.util.webhook_challenge(mode, token, challenge):
        return challenge

    raise HTTPException(status_code=403, detail="Forbidden")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
