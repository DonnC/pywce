import logging
from rich.console import Console
from rich.panel import Panel

from pywce import HookArg

logger = logging.getLogger(__name__)

def log_incoming_message(arg: HookArg) -> None:
    """
    log_incoming_message(arg: HookArg)

    A global pre-hook called everytime before any other hooks are processed.

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        None: global hooks have no need to return anything
    """
    panel = Panel.fit(f"[yellow]{arg.hook} {arg}", title="Incoming Hook Arg", subtitle="End Of Hook Arg")
    logger.debug(Console().print(panel))