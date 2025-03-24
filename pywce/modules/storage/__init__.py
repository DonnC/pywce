from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict

import ruamel.yaml

from pywce.src.exceptions import EngineException


class IStorageManager(ABC):
    """Abstract base class for different template storage backends."""

    @abstractmethod
    def load_templates(self) -> Dict:
        """Load chatbot templates."""
        pass

    @abstractmethod
    def load_triggers(self) -> Dict:
        """Load chatbot triggers."""
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a template exists."""
        pass

    @abstractmethod
    def triggers(self) -> Dict:
        """Get all triggers"""
        pass

    @abstractmethod
    def get(self, name: str) -> Optional[Dict]:
        """Load a single template by name."""
        pass


class YamlStorageManager(IStorageManager):
    """
        YAML files storage manager

        Read all yaml files
    """
    _TEMPLATES: Dict = {}
    _TRIGGERS: Dict = {}

    def __init__(self, template_dir: str, trigger_dir: str):
        self.template_dir = Path(template_dir)
        self.trigger_dir = Path(trigger_dir)
        self.yaml = ruamel.yaml.YAML()

        self.load_triggers()
        self.load_templates()

    def load_templates(self) -> Dict:
        self._TEMPLATES.clear()

        if not self.template_dir.is_dir():
            raise EngineException("Template dir provided is not a valid directory")

        for template_file in self.template_dir.glob("*.yaml"):
            with template_file.open("r", encoding="utf-8") as file:
                data = self.yaml.load(file)
                if data:
                    self._TEMPLATES.update(data)

        assert len(self._TEMPLATES) != 0, "No valid templates found"

        # TODO: remove me
        from pprint import pprint
        pprint(self._TEMPLATES)

        return self._TEMPLATES

    def load_triggers(self) -> Dict:
        self._TRIGGERS.clear()

        if not self.trigger_dir.is_dir():
            raise EngineException("Trigger dir provided is not a valid directory")

        for trigger_file in self.trigger_dir.glob("*.yaml"):
            with trigger_file.open("r", encoding="utf-8") as file:
                data = self.yaml.load(file)
                if data:
                    self._TRIGGERS.update(data)

        return self._TRIGGERS

    def exists(self, name: str) -> bool:
        return name in self._TEMPLATES

    def get(self, name: str) -> Optional[Dict]:
        return self._TEMPLATES.get(name)

    def triggers(self) -> Dict:
        return self._TRIGGERS
