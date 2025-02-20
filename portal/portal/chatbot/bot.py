import os
from typing import Dict

from fastapi import Response, Query, BackgroundTasks, Request

from pywce import client, Engine, EngineConfig, pywce_logger

logger = pywce_logger(__name__, False)

wa_config = client.WhatsAppConfig(
    token=os.getenv("ACCESS_TOKEN"),
    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
    hub_verification_token=os.getenv("WEBHOOK_HUB_TOKEN"),
    use_emulator=int(os.getenv("USE_EMULATOR", 0)) == 1
)

whatsapp = client.WhatsApp(whatsapp_config=wa_config)

engine_config = EngineConfig(
    whatsapp=whatsapp,
    templates_dir=os.getenv("TEMPLATES_DIR"),
    trigger_dir=os.getenv("TRIGGERS_DIR"),
    start_template_stage=os.getenv("START_STAGE"),
    ext_handler_hook=os.getenv("LIVE_SUPPORT_HOOK")
)

engine = Engine(config=engine_config)


# -  endpoint utilities -
async def _bg_webhook_event(payload: Dict, headers: Dict) -> None:
    logger.debug("Portal: received webhook event, processing..")
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)


async def ep_process_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    payload = await request.json()
    background_tasks.add_task(_bg_webhook_event, payload, dict(request.headers))
    return Response(content="ACK", status_code=200)


def ep_verify_webhook(
        mode: str = Query(..., alias="hub.mode"),
        token: str = Query(..., alias="hub.verify_token"),
        challenge: str = Query(..., alias="hub.challenge")
) -> Response:
    result = whatsapp.util.verify_webhook_verification_challenge(
        mode=mode, token=token, challenge=challenge
    )

    if result is None:
        return Response(content="Forbidden", status_code=403)

    return Response(content=result, status_code=200)
