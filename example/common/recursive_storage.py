import json
from pathlib import Path
from typing import Dict

import ruamel.yaml

from pywce.modules.storage import YamlJsonStorageManager
from pywce.src.constants import EngineConstants
from pywce.src.exceptions import EngineException


class RecursiveYamlJsonStorageManager(YamlJsonStorageManager):
    """
    Example-focused storage manager that loads templates and triggers recursively.

    This is useful for self-evolving bot examples where generated assets are written
    into nested folders like `generated/templates`.
    """

    def __init__(self, root_dir: str):
        self.template_dir = Path(root_dir)
        self.trigger_dir = Path(root_dir)
        self.yaml = ruamel.yaml.YAML()
        self.load_triggers()
        self.load_templates()
        self.validate()

    def load_templates(self) -> None:
        self._TEMPLATES.clear()

        if not self.template_dir.is_dir():
            raise EngineException("Template dir provided is not a valid directory")

        for template_file in self.template_dir.rglob("*"):
            if not template_file.is_file():
                continue
            if template_file.suffix not in [".yml", ".yaml", ".json"]:
                continue
            if "template" not in str(template_file.parent).lower():
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

        for trigger_file in self.trigger_dir.rglob("*"):
            if not trigger_file.is_file():
                continue
            if trigger_file.suffix not in [".yml", ".yaml", ".json"]:
                continue
            if "trigger" not in trigger_file.name.lower() and "trigger" not in str(trigger_file.parent).lower():
                continue

            with trigger_file.open("r", encoding="utf-8") as file:
                data = json.load(file) if trigger_file.suffix == ".json" else self.yaml.load(file)
                if data:
                    self._TRIGGERS.update(data)

