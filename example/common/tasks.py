from .config import engine


def engine_bg_task(payload: dict) -> None:
    engine.process_webhook(webhook_data=payload)
