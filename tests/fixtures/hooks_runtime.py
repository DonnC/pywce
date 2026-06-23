from pywce import HookArg, TemplateDynamicBody


def _append_event(arg: HookArg, name: str) -> HookArg:
    events = arg.session_manager.get_global("events") or []
    events.append(name)
    arg.session_manager.save_global("events", events)
    return arg


def start_on_receive(arg: HookArg) -> HookArg:
    return _append_event(arg, "on_receive")


def next_on_generate(arg: HookArg) -> HookArg:
    return _append_event(arg, "on_generate")


def render_name(arg: HookArg) -> HookArg:
    arg.template_body = TemplateDynamicBody(
        render_template_payload={"name": "TDD"}
    )
    return arg


def route_to_report(arg: HookArg) -> HookArg:
    arg.redirect_to = "REPORT"
    return arg

