from datetime import datetime

from pywce import hook, HookArg, client, pywce_logger, SessionConstants

_logger = pywce_logger(__name__)


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
    _logger.debug("AI toggle state hook arg: %s", arg)

    if arg.params.get("type", "TERMINATE") == "INVOKE":
        session_data = {
            "start": datetime.now().isoformat(),
            "agent": arg.user_input
        }
        arg.session_manager.save(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER,
                                 data=session_data)

        _logger.info(f"AI 🤖 agent {arg.user_input} - chatting with user begin!")
    else:
        session_data = arg.session_manager.get(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
        _logger.info(f"Terminating LS for, User: {arg.user.wa_id} | Data: {session_data}")

        arg.session_manager.evict(session_id=arg.user.wa_id, key=SessionConstants.EXTERNAL_CHAT_HANDLER)
        _logger.info(f"AI 🤖 agent {arg.user_input} - chat with user terminated!")

    return arg


@hook
def agent_processor(arg: HookArg) -> HookArg:
    """
    agent_processor(arg)

    This hook will provide:
    - Create a new agent
    - Get existing agents
    - Select an agent to use
    - Delete agent

    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """
    _logger.debug("AI hook arg: %s", arg)

    message_body: client.ResponseStructure = arg.user_input

    return arg
