from pywce import HookArg, pywce_logger

logger = pywce_logger(__name__)


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
    logger.warning(arg)
    logger.debug(f"{'*' * 30}")
