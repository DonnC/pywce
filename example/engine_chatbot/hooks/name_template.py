from pywce import HookArg, TemplateDynamicBody
from pywce.engine_logger import get_engine_logger

logger = get_engine_logger(__name__)

def username(arg: HookArg) -> HookArg:
    """
    A template to det default user whatsapp username.

    :param arg: HookArg passed by engine
    :return: updated HookArg
    """
    logger.info(f"Received hook arg: {arg}")

    # set default username in session for retrieving later
    arg.session_manager.save(session_id=arg.user.wa_id, key="username", data=arg.user.name)

    # set render payload data to match the required template dynamic var
    arg.template_body = TemplateDynamicBody(render_template_payload={"name": arg.user.name})

    return arg
