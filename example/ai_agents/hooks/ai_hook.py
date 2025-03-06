from datetime import datetime

from pywce import client, hook, HookArg, pywce_logger, SessionConstants, HookService, ai
from ..service.ai_agents import AiAgentService
from ...common.config import engine

_logger = pywce_logger(__name__)

_service = AiAgentService()

TERMINATION_COMMAND = "terminate"


@hook
def invoke_ai_agent(arg: HookArg) -> HookArg:
    """
    invoke_ai_agent(arg)

    Initiate external session handler

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """
    agent_id = arg.session_manager.get_from_props(arg.session_id, "selected_agent")

    session_data = {
        "start": datetime.now().isoformat(),
        "agent_id": agent_id
    }
    arg.session_manager.save(session_id=arg.session_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER,
                             data=session_data)

    return arg


async def agent_processor(arg: HookArg) -> None:
    """
    Receive user input and pass to AI for response.

    Return ai response to user as a computed whatsapp message

    If user provides a termination command, end handler session
    """
    _logger.warning("User input message: %s", arg.user_input)

    agent_id = arg.session_manager.get_from_props(arg.session_id, "selected_agent")

    if arg.user_input.typ == client.MessageTypeEnum.TEXT:
        user_input = arg.user_input.body.get("body")

    else:
        user_input = arg.user_input.body.get("id")

    _logger.warning("User input: %s", user_input)

    if user_input.lower() == TERMINATION_COMMAND.lower():
        _logger.debug("User consent to terminate, killing session..")
        kill_payload = ai.AiResponse(
            typ="button",
            message="You have terminated your conversation with an AI Agent.\nThank you, click the button to go to menu",
            title="Session Termination",
            options=["Menu"]
        )
        terminate_response = HookService.map_ai_handler_response(arg.session_id, kill_payload)
        await engine.ext_handler_respond(terminate_response)

        engine.terminate_external_handler(arg.session_id)
        return

    agent_name, response = _service.response(agent_id, arg.session_id, user_input)

    _logger.info("AI response: %s", response)

    mapped_response = HookService.map_ai_handler_response(arg.session_id, response, f"🤖{agent_name}")

    # return response to user
    channel_response = await engine.ext_handler_respond(mapped_response)

    _logger.info("AI response send to user: %s", channel_response)
