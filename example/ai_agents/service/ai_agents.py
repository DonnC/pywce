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

    def greeting(self, agent_name) -> str:
        if agent_name not in _agents:
            raise ValueError(f"AI agent: {agent_name} doesn't exist!")

        return f"Hi, I am {agent_name} 🤖!\n\nHow can I help you today?"

    def create(self, agent_name: str, agent_instructions: str) -> bool:
        if agent_name.lower() in _agents.keys():
            _logger.warning("Agent already exists!")
            return False

        _agents[agent_name.lower()] = ai.AiService(agent_name, agent_instructions, {})
        self.save_agents()
        return True

    def remove(self, agent_name: str) -> bool:
        if agent_name.lower() in _agents.keys():
            _agents.pop(agent_name.lower())
            self.save_agents()
            return True
        return False

    def list_agents(self) -> list:
        return list(_agents.keys())

    def response(self, agent_name: str, wa_id: str, message: str):
        if agent_name.lower() in _agents.keys():
            result = _agents.get(agent_name.lower()).generate_response(message, wa_id)
            _logger.debug(f"[Ai] Agent: %s, result: %s", agent_name, result)
            return result

        raise ValueError(f"AI agent: {agent_name} doesn't exist!")

    def save_agents(self):
        """Persists agent configurations to a JSON file."""
        data = {name: {"name": name, "instructions": agent.instructions} for name, agent in _agents.items()}

        with open(AGENT_FILE, "w") as f:
            json.dump(data, f, indent=4)

        _logger.info("Agents saved to JSON.")

    def load_agents(self):
        """Loads agent configurations from a JSON file on startup."""
        if not os.path.exists(AGENT_FILE):
            return

        try:
            if len(_agents) > 0:
                return

            with open(AGENT_FILE, "r") as f:
                data = json.load(f)
                for name, details in data.items():
                    _agents[name] = ai.AiService(details["name"], details["instructions"], {})

            _logger.info("Agents loaded from JSON.")

        except Exception as e:
            _logger.error(f"Error loading agents: {e}")
