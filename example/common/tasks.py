from .runtime_loader import get_engine


def engine_bg_task(payload: dict) -> None:
    get_engine().process_webhook(payload)
