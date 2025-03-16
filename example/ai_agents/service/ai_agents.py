import json
import os
from typing import Dict

from pywce import ai, pywce_logger

# JSON file to store AI agents
AGENT_FILE = "agents.json"

# container for all user defined agents
_agents: Dict[str, ai.AiService] = {}

_logger = pywce_logger(__name__)


class AiAgentService:
    """
          AI Agent Service.

          Ability to manage ai agents dynamically.
    """

    def __init__(self):
        """Load agents from JSON storage on startup."""
        self.load_agents()

    def _get_last_index(self) -> int:
        """Returns the next unique ID for a new agent."""
        return max((int(k) for k in _agents.keys()), default=-1) + 1

    @staticmethod
    def truncate_text(text: str, max_length: int = 72) -> str:
        """Truncate text to `max_length` characters, adding '...' if it exceeds the limit."""
        text = text.replace("\n", ", ")
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def greeting(self, agent_name) -> str:
        if agent_name not in _agents:
            raise ValueError(f"AI agent: {agent_name} doesn't exist!")

        return f"Hi, I am {agent_name} 🤖!\n\nHow can I help you today?"

    def create(self, agent_name: str, agent_instructions: str) -> bool:
        if agent_name.lower() in _agents.keys():
            _logger.warning("Agent already exists!")
            return False

        _agents[str(self._get_last_index())] = ai.AiService(agent_name, agent_instructions, {})
        self.save_agents()
        return True

    def remove(self, agent_id: str) -> bool:
        if agent_id in _agents.keys():
            _agents.pop(agent_id)
            self.save_agents()
            return True
        return False

    def list_agents(self) -> Dict[str, ai.AiService]:
        return _agents

    def response(self, agent_id: str, wa_id: str, message: str) -> tuple:
        # return (agent name, agent response)

        if agent_id in _agents.keys():
            agent = _agents[agent_id]
            result = agent.generate_response(message, wa_id)
            _logger.debug(f"[Ai] Agent Id: %s, result: %s", agent_id, result)
            return (agent.name, result)

        raise ValueError(f"AI agent with id: {agent_id} doesn't exist!")

    def save_agents(self):
        """Persists agent configurations to a JSON file."""
        data = {_id: {"name": agent.name, "instructions": agent.instructions} for _id, agent in _agents.items()}

        with open(AGENT_FILE, "w") as f:
            json.dump(data, f, indent=4)

        _logger.info("Agents saved to JSON.")

    def load_agents(self):
        """Loads agent configurations from a JSON file on startup."""
        _logger.debug("Loading persisted agents..")

        if not os.path.exists(AGENT_FILE):
            _logger.warning(f"Agent file: {AGENT_FILE} doesn't exist!")
            return

        try:
            if len(_agents) > 0:
                return

            with open(AGENT_FILE, "r") as f:
                data = json.load(f)
                for _id, details in data.items():
                    _agents[_id] = ai.AiService(details["name"], details["instructions"], {})

            _logger.info("Agents loaded from JSON.")

        except Exception as e:
            _logger.error(f"Error loading agents: {e}")
