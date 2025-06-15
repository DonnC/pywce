import logging
import time

from pywce import HookArg

logger = logging.getLogger(__name__)

def capture(arg: HookArg):
    """
    Simulate capturing user ride and saving to db or perform further actions

    :param arg: HookArg passed by the engine
    :return: updated HookArg
    """
    saved_user_props = arg.session_manager.get_user_props(session_id=arg.session_id)

    # simulate request processing
    time.sleep(10)

    if arg.user_input == 'confirm':
        logger.debug(f"Current user props: %s", saved_user_props)
        # TODO: implement logic

    return arg
