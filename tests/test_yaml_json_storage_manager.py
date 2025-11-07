import os
import unittest
from pathlib import Path

from pywce import storage
from pywce.src.exceptions import EngineException
from pywce.src.templates import EngineRoute


class TestYamlJsonStorageManager(unittest.TestCase):
    def setUp(self):
        current_dir = Path(__file__).parent

        self.valid_template_dir = current_dir / "fixtures" / "templates"
        self.valid_trigger_dir = current_dir / "fixtures" / "triggers"
        self.invalid_dir = current_dir / "fixtures" / "invalid"

        # Create directories and sample files
        os.makedirs(self.valid_template_dir, exist_ok=True)
        os.makedirs(self.valid_trigger_dir, exist_ok=True)

        self.manager = storage.YamlJsonStorageManager(
            str(self.valid_template_dir),
            str(self.valid_trigger_dir)
        )

    def test_initialization_with_valid_directories(self):
        self.assertEqual(self.valid_template_dir, self.manager.template_dir)
        self.assertEqual(self.valid_trigger_dir, self.manager.trigger_dir)

    def test_initialization_with_invalid_directory(self):
        with self.assertRaises(EngineException) as context:
            storage.YamlJsonStorageManager(str(self.invalid_dir), str(self.invalid_dir))
        self.assertIn("provided is not a valid directory", str(context.exception))

    def test_load_templates_with_valid_files(self):
        self.manager.load_templates()
        self.assertGreater(len(self.manager._TEMPLATES), 0)

    def test_load_triggers_with_valid_files(self):
        self.manager.load_triggers()
        self.assertGreater(len(self.manager._TRIGGERS), 0)

    def test_exists_with_valid_name(self):
        self.manager.load_templates()
        self.assertTrue(self.manager.exists("REPORT"))

    def test_exists_with_invalid_name(self):
        self.manager.load_templates()
        self.assertFalse(self.manager.exists("non_existent_template"))

    def test_get_with_valid_name(self):
        self.manager.load_templates()
        template = self.manager.get("REPORT")
        self.assertIsNotNone(template)

    def test_get_with_invalid_name(self):
        self.manager.load_templates()
        template = self.manager.get("non_existent_template")
        self.assertIsNone(template)

    def test_triggers_list_generation(self):
        self.manager.load_triggers()
        triggers = self.manager.triggers()
        self.assertGreater(len(triggers), 0)
        self.assertTrue(all(isinstance(trigger, EngineRoute) for trigger in triggers))


if __name__ == '__main__':
    unittest.main()
