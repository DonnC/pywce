import logging

from pywce import HookArg, hook

logger = logging.getLogger(__name__)

@hook
def capture(arg: HookArg):
    """
    Simulate capturing user ride and saving to db or perform further actions

    :param arg: HookArg passed by the engine
    :return: updated HookArg
    """
    logger.debug(f"Capturing ride: %s", arg)

    session_id = arg.user.wa_id
    session = arg.session_manager

    if arg.user_input == 'confirm':
        # perform further actions
        logger.debug(f"Current user props: %s", session.get_user_props(session_id=session_id))

    return arg
