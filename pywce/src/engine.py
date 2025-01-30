from pathlib import Path
from typing import Dict, Any

import ruamel.yaml

from pywce.engine_logger import get_engine_logger
from pywce.src.models import PywceEngineConfig, WorkerJob
from pywce.src.services import Worker

_logger = get_engine_logger(__name__)


class PywceEngine:
    _TEMPLATES: Dict = {}
    _TRIGGERS: Dict = {}

    def __init__(self, config: PywceEngineConfig):
        self.config: PywceEngineConfig = config
        self.whatsapp = config.whatsapp

        self._load_resources()

    def _load_resources(self):
        """
        Load all YAML files once from a directory and merge them into a single dictionary.
        """
        self._TEMPLATES.clear()
        self._TRIGGERS.clear()

        yaml = ruamel.yaml.YAML()

        template_path = Path(self.config.templates_dir)
        trigger_path = Path(self.config.trigger_dir)

        if not template_path.is_dir() or not trigger_path.is_dir():
            raise ValueError(f"Template or trigger dir provided is not a valid directory")

        _logger.debug(f"Loading templates from dir: {template_path}")

        for template_file in template_path.glob("*.yaml"):
            with template_file.open("r", encoding="utf-8") as file:
                data = yaml.load(file)
                if data:
                    self._TEMPLATES.update(data)

        _logger.debug(f"Loading triggers from dir: {trigger_path}")
        for trigger_file in trigger_path.glob("*.yaml"):
            with trigger_file.open("r", encoding="utf-8") as file:
                data = yaml.load(file)
                if data:
                    self._TRIGGERS.update(data)

    def get_templates(self) -> Dict:
        return self._TEMPLATES

    def get_triggers(self) -> Dict:
        return self._TRIGGERS

    def verify_webhook(self, mode, challenge, token):
        return self.whatsapp.util.verify_webhook_verification_challenge(mode, challenge, token)

    async def process_webhook(self, webhook_data: Dict[str, Any], webhook_headers: Dict[str, Any]):
        if self.whatsapp.util.verify_webhook_payload(
                webhook_payload=webhook_data,
                webhook_headers=webhook_headers
        ):
            if not self.whatsapp.util.is_valid_webhook_message(webhook_data):
                _logger.warning("Invalid webhook message, skipping..")
                return

            worker = Worker(
                job=WorkerJob(
                    engine_config=self.config,
                    payload=self.whatsapp.util.get_response_structure(webhook_data),
                    user=self.whatsapp.util.get_wa_user(webhook_data),
                    templates=self._TEMPLATES,
                    triggers=self._TRIGGERS
                )
            )

            # process current webhook request
            await worker.work()

        else:
            _logger.warning("Invalid webhook payload")
            return
