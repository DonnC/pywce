from pywce import hook, HookArg, TemplateDynamicBody

@hook
def username(arg: HookArg) -> HookArg:
    """
    A templates to get default user whatsapp username.

    :param arg: HookArg passed by engine
    :return: updated HookArg
    """
    print(f"Received hook arg: {arg}")

    # set default username in session for retrieving later
    arg.session_manager.save(session_id=arg.user.wa_id, key="username", data=arg.user.name)

    # set render payload data to match the required templates dynamic var
    arg.template_body = TemplateDynamicBody(render_template_payload={"name": arg.user.name})

    return arg
