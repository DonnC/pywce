from pywce import hook, HookArg, TemplateDynamicBody, template


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

    # ['empty trash', 'collect rent', 'visit Auntie', 'debug code']
    tasks: list = arg.session_manager.get(session_id=arg.session_id, key="tasks")

    if 1 < len(tasks) < 3:
        tpl = template.ButtonTemplate(
            message=template.ButtonMessage(
                buttons=tasks,
                title="Tasks",
                body="Select your task to manage it"
            )
        )

    else:
        tpl = template.TextTemplate(
            message="You do not have any tasks. Add tasks to view them"
        )

    arg.template_body = TemplateDynamicBody(initial_flow_payload=tpl)

    return arg
