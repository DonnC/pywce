from pywce import HookArg, pywce_logger, hook

logger = pywce_logger(__name__, False)

@hook
def capture(arg: HookArg):
    """
    Capture ride business logic implementation

    :param arg: HookArg passed by the engine
    :return: updated HookArg
    """
    logger.debug(f"Capture ride hook: {arg}")

    session_id = arg.user.wa_id
    session = arg.session_manager

    if arg.user_input == 'confirm':
        # TODO: implement business logic
        logger.info("Current user props")
        logger.info(session.get_user_props(session_id=session_id))

    return arg
