import json
import tempfile
import unittest
from pathlib import Path

from pywce import storage
from pywce.src.exceptions import EngineException


class TestFlowValidation(unittest.TestCase):
    def _write_yaml(self, path: Path, content: str):
        path.write_text(content, encoding="utf-8")

    def _write_json(self, path: Path, content: dict):
        path.write_text(json.dumps(content), encoding="utf-8")

    def test_missing_route_target_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates_dir = root / "templates"
            triggers_dir = root / "triggers"
            templates_dir.mkdir()
            triggers_dir.mkdir()

            self._write_yaml(
                templates_dir / "templates.yaml",
                """
"START-MENU":
  kind: button
  message:
    title: Start
    body: Choose
    buttons:
      - Begin
  routes:
    "begin": "MISSING-STAGE"
"""
            )
            self._write_yaml(triggers_dir / "triggers.yaml", "")

            with self.assertRaises(EngineException) as ctx:
                storage.YamlJsonStorageManager(str(templates_dir), str(triggers_dir))

            self.assertIn("unknown next stage", str(ctx.exception).lower())

    def test_invalid_template_kind_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates_dir = root / "templates"
            triggers_dir = root / "triggers"
            templates_dir.mkdir()
            triggers_dir.mkdir()

            self._write_yaml(
                templates_dir / "templates.yaml",
                """
"START-MENU":
  kind: mystery
  message: Hello
  routes:
    "re:.*": "START-MENU"
"""
            )
            self._write_yaml(triggers_dir / "triggers.yaml", "")

            with self.assertRaises(EngineException) as ctx:
                storage.YamlJsonStorageManager(str(templates_dir), str(triggers_dir))

            self.assertIn("invalid template", str(ctx.exception).lower())

    def test_trigger_target_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates_dir = root / "templates"
            triggers_dir = root / "triggers"
            templates_dir.mkdir()
            triggers_dir.mkdir()

            self._write_json(
                templates_dir / "templates.json",
                {
                    "START-MENU": {
                        "kind": "text",
                        "message": "Hello",
                        "routes": {"re:.*": "START-MENU"}
                    }
                }
            )
            self._write_yaml(
                triggers_dir / "triggers.yaml",
                """
"REPORT": "re:(?i)^report$"
"""
            )

            with self.assertRaises(EngineException) as ctx:
                storage.YamlJsonStorageManager(str(templates_dir), str(triggers_dir))

            self.assertIn("unknown trigger stage", str(ctx.exception).lower())

    def test_invalid_hook_path_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates_dir = root / "templates"
            triggers_dir = root / "triggers"
            templates_dir.mkdir()
            triggers_dir.mkdir()

            self._write_yaml(
                templates_dir / "templates.yaml",
                """
"START-MENU":
  kind: text
  on-receive: tests.fixtures.hooks_runtime.missing_hook
  message: Hello
  routes:
    "re:.*": "START-MENU"
"""
            )
            self._write_yaml(triggers_dir / "triggers.yaml", "")

            with self.assertRaises(EngineException) as ctx:
                storage.YamlJsonStorageManager(str(templates_dir), str(triggers_dir))

            self.assertIn("invalid hook", str(ctx.exception).lower())

    def test_missing_required_message_field_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates_dir = root / "templates"
            triggers_dir = root / "triggers"
            templates_dir.mkdir()
            triggers_dir.mkdir()

            self._write_yaml(
                templates_dir / "templates.yaml",
                """
"START-MENU":
  kind: button
  message:
    title: Start
    body: Choose
  routes:
    "re:.*": "START-MENU"
"""
            )
            self._write_yaml(triggers_dir / "triggers.yaml", "")

            with self.assertRaises(EngineException) as ctx:
                storage.YamlJsonStorageManager(str(templates_dir), str(triggers_dir))

            self.assertIn("invalid template", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
