import logging
from dataclasses import asdict

from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from pywce import HookArg, client, FlowEndpointException
from .data import LocalDataSource

logger = logging.getLogger(__name__)

def log_incoming_message(arg: HookArg, title: str = None) -> None:
    """
    log_incoming_message(arg: HookArg)

    A global pre-hook called everytime before any other hooks are processed.

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        None: global hooks have no need to return anything
    """
    panel_title = title if title is not None else "HookArg | Global"
    panel = Panel.fit(Pretty(arg), title=panel_title, subtitle=f"{arg.hook}")
    logger.debug(Console().print(panel, highlight=True))


def flow_endpoint_handler(payload: client.FlowEndpointPayload) -> dict:
    """
    Handles all flow endpoint requests, the callable receives payload already decrypted
    """

    arg = HookArg(
        hook="flow_endpoint_handler",
        additional_data=asdict(payload),
        user=client.WaUser(),
        session_id=''
    )

    log_incoming_message(arg)

    response = {}

    action = payload.data.get('type')

    if action == 'time_slots':
        response = LocalDataSource.flow_time_slots

    # TODO: handle other logic

    return response
