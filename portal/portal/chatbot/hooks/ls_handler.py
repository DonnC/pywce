from pywce import hook, HookArg, pywce_logger
from ...state import ChatState

logger = pywce_logger(__name__)


@hook
def live_support_handler(arg: HookArg) -> HookArg:
    """
        On new hook event, update portal state on user message
    """
    logger.info(f"Received LS handler hook arg: {arg}")

    # send user message to portal admin
    ChatState.receive_message(
        sender=arg.session_id,
        message=arg.user_input
    )

    logger.debug("Chat message event sent to portal agent")

    return arg
