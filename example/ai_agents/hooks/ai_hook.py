from datetime import datetime

from pywce import client, hook, HookArg, pywce_logger, SessionConstants, HookService
from ..service.ai_agents import AiAgentService
from ...common.config import engine

_logger = pywce_logger(__name__)

_service = AiAgentService()


@hook
def toggle_agent_state(arg: HookArg) -> HookArg:
    """
    toggle_agent_state(arg)

    Initiate external session handler or terminate it

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """
    agent_id = arg.session_manager.get_from_props(arg.session_id, "selected_agent")

    _logger.debug("Selected agent id : %s", agent_id)

    if arg.params.get("type", "TERMINATE") == "INVOKE":
        session_data = {
            "start": datetime.now().isoformat(),
            "agent_id": agent_id
        }
        arg.session_manager.save(session_id=arg.session_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER,
                                 data=session_data)

        _logger.info(f"AI 🤖 agent with id {arg.user_input} - chatting with user begin!")
    else:
        session_data = arg.session_manager.get(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
        _logger.info(f"Terminating LS for, User: {arg.user.wa_id} | Data: {session_data}")

        arg.session_manager.evict(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
        _logger.info(f"AI 🤖 agent with id {arg.user_input} - chat with user terminated!")

    return arg


async def agent_processor(arg: HookArg) -> None:
    """
    Receive user input and pass to AI for response.

    Return ai response to user as a computed whatsapp message

    TODO: support other user input message types
    """
    _logger.warning("User input message: %s", arg.user_input)

    agent_id = arg.session_manager.get_from_props(arg.session_id, "selected_agent")

    if arg.user_input.typ == client.MessageTypeEnum.TEXT:
        user_input = arg.user_input.body.get("body")

    else:
        user_input = arg.user_input.body.get("id")

    _logger.warning("User input: %s", user_input)

    agent_name, response = _service.response(agent_id, arg.session_id, user_input)

    _logger.info("AI response: %s", response)

    mapped_response = HookService.map_ai_handler_response(arg.session_id, response, f"🤖{agent_name}")

    # return response to user
    channel_response = await engine.ext_handler_respond(mapped_response)

    _logger.info("AI response send to user: %s", channel_response)
