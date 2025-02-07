import json

from pywce import hook, HookArg, pywce_logger
from ...constants import PubSubChannel
from ...redis_manager import RedisManager

logger = pywce_logger(__name__, False)
redis_manager = RedisManager()


@hook
def live_support_handler(arg: HookArg) -> HookArg:
    """
        On new hook event, publish to pub/sub channel
        to be processed by agent on portal
    """
    logger.info(f"Received LS handler hook arg: {arg}")

    redis_manager.get_instance().publish(
        channel=PubSubChannel.INCOMING,
        message=json.dumps({
            "recipient_id": arg.user.wa_id,
            "message": arg.user_input,
        })
    )

    logger.debug("Chat message event sent to portal agent")

    return arg
