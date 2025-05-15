import logging

from pywce import HookArg, TemplateDynamicBody

logger = logging.getLogger(__name__)


def log_incoming_message(arg: HookArg) -> None:
    """
    initiate(arg: HookArg)

    A global pre-hook called everytime & before any other hooks are processed.

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        None: global hooks have no need to return anything
    """
    logger.debug(f"{'*' * 10} New incoming request arg {'*' * 10}")
    logger.debug("%s", arg)
    logger.debug(f"{'*' * 30}")


def external_hook_processor(arg: HookArg) -> HookArg:
    """
    initiate(arg: HookArg)

    A global pre-hook called everytime & before any other hooks are processed.

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        None: global hooks have no need to return anything
    """
    logger.debug(f"{'*' * 10} external hook processor {'*' * 10}")
    logger.debug("%s", arg)
    logger.debug(f"{'*' * 30}")

    # set default username in session for retrieving later
    arg.session_manager.save(session_id=arg.user.wa_id, key="username", data=arg.user.name)

    # set render payload data to match the required templates dynamic var
    arg.template_body = TemplateDynamicBody(render_template_payload={"name": arg.user.name})

    return arg
