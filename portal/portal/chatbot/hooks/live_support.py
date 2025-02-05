from datetime import datetime

from ...data import put_global, clear_global_entry, evict_global
from ...state import ChatState
from pywce import hook, HookArg, pywce_logger, SessionConstants

logger = pywce_logger(__name__)


@hook
def live_support(arg: HookArg) -> HookArg:
    """
    Initiate live support or terminate current session
    """
    logger.info(f"Received hook arg: {arg}")

    if arg.params.get("type", "TERMINATE") == "REQUEST":
        ls_data = datetime.now().isoformat()

        arg.session_manager.save(session_id=arg.user.wa_id, key=SessionConstants.LIVE_SUPPORT, data=ls_data)

        logger.info("Attempting to request LS admin")

        put_global(arg.session_id, [f"Hello, User: {arg.user.name} is waiting in the lobby!"])

        logger.info(f"Live support agent notified - {arg.user.wa_id}")
    else:
        ls_entry = arg.session_manager.get(session_id=arg.user.wa_id, key=SessionConstants.LIVE_SUPPORT)
        logger.info(f"Terminating LS for, User: {arg.user.wa_id} | Stats: {ls_entry}")

        arg.session_manager.evict(session_id=arg.user.wa_id, key=SessionConstants.LIVE_SUPPORT)
        evict_global(key=arg.user.wa_id)
        logger.warning("Live support terminated!")

    return arg
