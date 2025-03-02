from .config import engine


async def engine_bg_task(payload: dict, headers: dict) -> None:
    await engine.process_webhook(webhook_data=payload, webhook_headers=headers)
