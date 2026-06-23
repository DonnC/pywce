import logging
from abc import ABC, abstractmethod
from pathlib import Path
import json
from typing import Dict, List, Optional

import ruamel.yaml

from pywce.src.constants import EngineConstants
from pywce.src.exceptions import EngineException
from pywce.src.templates import EngineTemplate, Template
from pywce.src.templates.base_model import EngineRoute

_logger = logging.getLogger(__name__)

class IStorageManager(ABC):
    """Abstract base class for different templates storage backends."""

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
        """Check if a templates exists."""
        pass

    @abstractmethod
    def triggers(self) -> List[EngineRoute]:
        """Get all triggers"""
        pass

    @abstractmethod
    def get(self, name: str) -> Optional[EngineTemplate]:
        """Load a single templates by name."""
        pass

    @abstractmethod
    def validate(self) -> None:
        """Validate loaded templates and triggers."""
        pass


class YamlJsonStorageManager(IStorageManager):
    """
    YAML/JSON files storage manager.

    Supports reading both YAML (.yaml) and JSON (.json) files from the templates and triggers directories.
    """
    _TEMPLATES: Dict = {}
    _TRIGGERS: Dict = {}

    def __init__(self, template_dir: str, trigger_dir: str):
        self.template_dir = Path(template_dir)
        self.trigger_dir = Path(trigger_dir)
        self.yaml = ruamel.yaml.YAML()

        self.load_triggers()
        self.load_templates()
        self.validate()

    def load_templates(self) -> None:
        self._TEMPLATES.clear()

        if not self.template_dir.is_dir():
            raise EngineException("Template dir provided is not a valid directory")

        for template_file in self.template_dir.glob("*"):
            if template_file.suffix not in [".yml", ".yaml", ".json"]:
                continue

            with template_file.open("r", encoding="utf-8") as file:
                data = json.load(file) if template_file.suffix == ".json" else self.yaml.load(file)
                if data:
                    self._TEMPLATES.update(data)

        if not self._TEMPLATES:
            raise EngineException("No valid templates found")

    def load_triggers(self) -> None:
        self._TRIGGERS.clear()

        if not self.trigger_dir.is_dir():
            raise EngineException("Trigger dir provided is not a valid directory")

        for trigger_file in self.trigger_dir.glob("*"):
            if trigger_file.suffix not in [".yml", ".yaml", ".json"]:
                continue

            with trigger_file.open("r", encoding="utf-8") as file:
                data = json.load(file) if trigger_file.suffix == ".json" else self.yaml.load(file)
                if data:
                    self._TRIGGERS.update(data)

    def exists(self, name: str) -> bool:
        return name in self._TEMPLATES

    def get(self, name: str) -> Optional[EngineTemplate]:
        try:
            return Template.as_model(self._TEMPLATES.get(name))
        except Exception as e:
            _logger.error("Load template: %s, error: %s", name, str(e))
            return None

    def validate(self) -> None:
        from pywce.src.services import HookService

        validated_templates: Dict[str, EngineTemplate] = {}

        for name, raw_template in self._TEMPLATES.items():
            try:
                validated_templates[name] = Template.as_model(raw_template)
            except Exception as e:
                raise EngineException(f"Invalid template '{name}': {e}")

        for name, template in validated_templates.items():
            for hook_name in [
                template.template,
                template.on_receive,
                template.on_generate,
                template.router,
                template.middleware,
            ]:
                if hook_name is None:
                    continue

                try:
                    HookService.load_function(hook_name)
                except Exception as e:
                    raise EngineException(
                        f"Invalid hook '{hook_name}' in template '{name}': {e}"
                    )

            for route in template.routes:
                if route.next_stage not in validated_templates:
                    raise EngineException(
                        f"Template '{name}' has unknown next stage '{route.next_stage}'"
                    )

        for next_stage, user_input in self._TRIGGERS.items():
            if next_stage not in validated_templates:
                raise EngineException(
                    f"Unknown trigger stage '{next_stage}'"
                )

            try:
                EngineRoute(
                    user_input=user_input,
                    next_stage=next_stage,
                    is_regex=str(user_input).startswith(EngineConstants.REGEX_PLACEHOLDER)
                )
            except Exception as e:
                raise EngineException(f"Invalid trigger for stage '{next_stage}': {e}")

    def triggers(self) -> List[EngineRoute]:
        return [
            EngineRoute(user_input=v, next_stage=k, is_regex=str(v).startswith(EngineConstants.REGEX_PLACEHOLDER))
            for k, v in self._TRIGGERS.items()
        ]
