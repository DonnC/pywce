from .config import engine


def engine_bg_task(payload: dict, headers: dict) -> None:
    engine.process_webhook(webhook_data=payload, webhook_headers=headers)
