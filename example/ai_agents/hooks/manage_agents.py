from typing import Dict

from example.ai_agents.service.ai_agents import AiAgentService
from pywce import hook, HookArg, pywce_logger, TemplateDynamicBody, TemplateTypeConstants, ai

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
    agents: Dict[str, ai.AiService] = _service.list_agents()

    if len(agents) < 1:
        arg.template_body = TemplateDynamicBody(
            typ=TemplateTypeConstants.BUTTON,
            render_template_payload={
                "buttons": ["Menu"],
                "title": "AI Agents",
                "body": "No AI agents found. Kindly add new personalized agents to start"
            }
        )

    else:
        sections = {
            "Agents": {
                key: {"title": f"🤖 {value.name}", "description": AiAgentService.truncate_text(value.instructions)}
                for key, value in agents.items()
            }
        }

        arg.template_body = TemplateDynamicBody(
            typ=TemplateTypeConstants.LIST,
            render_template_payload={
                "button": "Select Agent",
                "title": "AI Agents 🤖",
                "body": "You have AI Agents available, click the button below to select an agent to interact with",
                "sections": sections
            }
        )

    return arg
