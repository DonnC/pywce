from abc import ABC, abstractmethod
from pathlib import Path
from pprint import pprint
from typing import Optional, Dict, List

import ruamel.yaml

from pywce.src.constants import EngineConstants
from pywce.src.exceptions import EngineException
from pywce.src.models.template.base_model import EngineRoute
from pywce.src.models.template.templates import EngineTemplate, load_template


class IStorageManager(ABC):
    """Abstract base class for different template storage backends."""

    @abstractmethod
    def load_templates(self) -> None:
        """Load chatbot templates."""
        pass

    @abstractmethod
    def load_triggers(self) -> None:
        """Load chatbot triggers."""
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a template exists."""
        pass

    @abstractmethod
    def triggers(self) -> List[EngineRoute]:
        """Get all triggers"""
        pass

    @abstractmethod
    def get(self, name: str) -> EngineTemplate:
        """Load a single template by name."""
        pass


class YamlStorageManager(IStorageManager):
    """
        YAML files storage manager

        Read all yaml files
    """
    _TEMPLATES: Dict = {}
    _TRIGGERS: Dict = {}

    def _map(self):
        for stage, template in self._TEMPLATES.items():
            print('[*] Processing template stage: {}'.format(stage))
            tpl = load_template(template)
            pprint(tpl)
            print('=' * 30)
            print()

    def __init__(self, template_dir: str, trigger_dir: str):
        self.template_dir = Path(template_dir)
        self.trigger_dir = Path(trigger_dir)
        self.yaml = ruamel.yaml.YAML()

        self.load_triggers()
        self.load_templates()
        self._map()

    def load_templates(self) -> None:
        self._TEMPLATES.clear()

        if not self.template_dir.is_dir():
            raise EngineException("Template dir provided is not a valid directory")

        for template_file in self.template_dir.glob("*.yaml"):
            with template_file.open("r", encoding="utf-8") as file:
                data = self.yaml.load(file)
                if data:
                    self._TEMPLATES.update(data)

        assert len(self._TEMPLATES) != 0, "No valid templates found"

    def load_triggers(self) -> None:
        self._TRIGGERS.clear()

        if not self.trigger_dir.is_dir():
            raise EngineException("Trigger dir provided is not a valid directory")

        for trigger_file in self.trigger_dir.glob("*.yaml"):
            with trigger_file.open("r", encoding="utf-8") as file:
                data = self.yaml.load(file)
                if data:
                    self._TRIGGERS.update(data)

    def exists(self, name: str) -> bool:
        return name in self._TEMPLATES

    def get(self, name: str) -> Optional[EngineTemplate]:
        tpl = self._TEMPLATES.get(name)
        return load_template(tpl)

    def triggers(self) -> List[EngineRoute]:
        return [
            EngineRoute(user_input=v, next_stage=k, is_regex=str(v).startswith(EngineConstants.REGEX_PLACEHOLDER))
            for k, v in self._TRIGGERS.items()
        ]
