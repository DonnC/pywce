import logging
from dataclasses import asdict

from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from pywce import HookArg, client, TemplateDynamicBody, FlowEndpointException
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


def flow_endpoint_handler(payload: client.FlowEndpointPayload) -> HookArg:
    """
    Handles all flow endpoint requests, the callable receives payload already decrypted

    The response will be passed in the `arg.template_body.flow_payload`

    This example follows the WhatsApp Flows endpoint sample flow for PreApproved Loan
    """

    arg = HookArg(
        hook="flow_endpoint_handler",
        additional_data=asdict(payload),
        user=client.WaUser(),
        session_id=''
    )

    log_incoming_message(arg)

    response = {}

    if payload.action == client.WhatsApp.PING_FLOW_ACTION:
        response = client.WhatsApp.FLOW_ENDPOINT_PING_PAYLOAD

    elif payload.data.get("error") is not None or payload.data.get("error_message") is not None:
        response = client.WhatsApp.FLOW_ENDPOINT_ACK_ERROR_PAYLOAD

    else:
        if payload.flow_token != LocalDataSource.expected_flow_token:
            raise FlowEndpointException(message="Unexpected token", data=client.WhatsApp.INVALID_FLOW_TOKEN_HTTP_CODE)

        if payload.action == client.WhatsApp.INIT_FLOW_ACTION:
            response = LocalDataSource.init_response

        # TODO: handle other logic

    arg.template_body = TemplateDynamicBody(flow_payload=response)

    return arg
