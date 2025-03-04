from example.ai_agents.service.ai_agents import AiAgentService
from pywce import hook, HookArg, pywce_logger, TemplateDynamicBody, TemplateTypeConstants

_logger = pywce_logger(__name__)

_service = AiAgentService()


@hook
def create(arg: HookArg) -> HookArg:
    """
    create new ai agent
    Args:
        arg (HookArg): pass hook argument from engine

    Returns:
        HookArg: the passed hook argument
    """
    _logger.debug("AI create hook arg: %s", arg)

    payload = arg.additional_data

    # TODO: use alias and files

    if _service.create(agent_name=payload["name"], agent_instructions=payload["instructions"]):
        _logger.debug("AI agent created!")

    return arg


@hook
def select_agent(arg: HookArg) -> HookArg:
    """
    render a list of agents to choose from
    """
    if len(_service.list_agents()) < 1:
        arg.template_body = TemplateDynamicBody(
            typ=TemplateTypeConstants.BUTTON,
            render_template_payload={
                "buttons": ["Menu"],
                "title": "AI Agents",
                "body": "No AI agents found. Kindly add new personalized agents to start"
            }
        )

    else:
        rendered_agents = {}
        for agent in _service.list_agents():
            rendered_agents[agent.lower()] = {"id": agent}

        arg.template_body = TemplateDynamicBody(
            typ=TemplateTypeConstants.LIST,
            render_template_payload={
                "buttons": ["Menu"],
                "title": "AI Agents",
                "body": "No AI agents found. Kindly add new personalized agents to start",
                "sections": {
                    "Agents": rendered_agents
                }
            }
        )

    return arg
