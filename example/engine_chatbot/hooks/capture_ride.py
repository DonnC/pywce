from pywce import HookArg, ISessionManager
from pywce.engine_logger import get_engine_logger

logger = get_engine_logger(__name__)


def capture(arg: HookArg):
    """
    Simulate capturing user ride and saving to db or perform further actions
    :param arg: HookArg passed by the engine
    :return: updated HookArg
    """
    logger.debug(f"Capturing ride: {arg}")

    session_id = arg.user.wa_id
    session: ISessionManager = arg.session_manager

    if arg.user_input == 'confirm':
        # perform further actions
        logger.info(f"Ride Type: {session.get_from_props(session_id=session_id, prop_key='ride_type')}")
        logger.info(f"Client Comments: {session.get_from_props(session_id=session_id, prop_key='ride_comments')}")

    return arg
