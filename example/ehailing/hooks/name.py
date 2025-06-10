from pywce import HookArg, TemplateDynamicBody

def username(arg: HookArg) -> HookArg:
    """
    A templates to get default user whatsapp username.

    :param arg: HookArg passed by engine
    :return: updated HookArg
    """
    default_wa_name= arg.user.name
    template_result = {"name": default_wa_name}

    # set default whatsapp name under `username` key in session for retrieving later
    arg.session_manager.save(session_id=arg.session_id, key="username", data=default_wa_name)

    # set render payload data to match the required templates dynamic var
    arg.template_body = TemplateDynamicBody(render_template_payload=template_result)

    return arg