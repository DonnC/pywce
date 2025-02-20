import json
from datetime import datetime

from pywce import hook, HookArg, pywce_logger, SessionConstants
from ...constants import PubSubChannel
from ...redis_manager import RedisManager

logger = pywce_logger(__name__, False)
redis_manager = RedisManager()


@hook
def live_support(arg: HookArg) -> HookArg:
    """
        Perform 2 tasks:
        1. Initiate live support
        2. terminate current session from bot
    """
    logger.info(f"Received hook arg: {arg}")

    if arg.params.get("type", "TERMINATE") == "REQUEST":
        ls_data = datetime.now().isoformat()

        arg.session_manager.save(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER, data=ls_data)

        logger.info("Attempting to request LS admin")

        redis_manager.get_instance().publish(
            channel=PubSubChannel.INCOMING,
            message=json.dumps({
                "recipient_id": arg.user.wa_id,
                "message": f"Hi, User<{arg.user.name}> is waiting in the lobby!",
            })
        )

        logger.info(f"Live support agent notified - {arg.user.wa_id}")
    else:
        ls_entry = arg.session_manager.get(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
        logger.info(f"Terminating LS for, User: {arg.user.wa_id} | Stats: {ls_entry}")

        arg.session_manager.evict(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
        logger.warning("Live support terminated!")

        redis_manager.get_instance().publish(
            channel=PubSubChannel.INCOMING,
            message=json.dumps({
                "recipient_id": arg.user.wa_id,
                "message": f"User<{arg.user.name}> terminated session!",
            })
        )

    return arg
