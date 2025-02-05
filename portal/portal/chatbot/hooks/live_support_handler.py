from pywce import hook, HookArg, pywce_logger
from ...data import fetch_global, put_global

logger = pywce_logger(__name__)


@hook
def live_support_handler(arg: HookArg) -> HookArg:
    """
        On new hook event, update portal state on user message
    """
    logger.info(f"Received LS handler hook arg: {arg}")

    queue: list[str] = fetch_global(key=arg.session_id)

    queue.append(arg.user_input)

    put_global(arg.session_id, queue)

    logger.debug("Chat message event sent to portal agent")

    return arg
