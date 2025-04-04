from pywce import HookArg, hook

@hook
def capture(arg: HookArg):
    """
    Simulate capturing user ride and saving to db or perform further actions

    :param arg: HookArg passed by the engine
    :return: updated HookArg
    """
    print(f"Capturing ride: {arg}")

    session_id = arg.user.wa_id
    session = arg.session_manager

    if arg.user_input == 'confirm':
        # perform further actions
        print(f"Current user props: {session.get_user_props(session_id=session_id)}")

    return arg
