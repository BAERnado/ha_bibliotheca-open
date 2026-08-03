"""Small repository checks that do not require Home Assistant."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "bibliotheca_open"


class StructureTest(unittest.TestCase):
    def test_manifest_and_translations(self) -> None:
        manifest = json.loads((COMPONENT / "manifest.json").read_text())

        self.assertTrue(manifest["config_flow"])
        self.assertEqual("cloud_polling", manifest["iot_class"])
        self.assertEqual("0.4.1", manifest["version"])
        self.assertTrue((COMPONENT / "event.py").is_file())
        self.assertEqual(
            [
                "bibliotheca-open-client@git+https://github.com/BAERnado/"
                "bibliotheca-open-client.git@2c970aa"
            ],
            manifest["requirements"],
        )
        for language in ("de", "en"):
            translation = json.loads(
                (COMPONENT / "translations" / f"{language}.json").read_text()
            )
            self.assertIn("renew_loan", translation["services"])
            self.assertIn("update_interval", translation["options"]["step"]["init"]["data"])
            self.assertIn("due_soon_days", translation["options"]["step"]["init"]["data"])
        self.assertIn("Apache License", (ROOT / "LICENSE").read_text())
        self.assertIn("Copyright 2026 BAERnado", (ROOT / "NOTICE").read_text())

    def test_activity_is_published_and_stale_loans_are_removed(self) -> None:
        event_source = (COMPONENT / "event.py").read_text()
        sensor_source = (COMPONENT / "sensor.py").read_text()

        self.assertIn("self.async_write_ha_state()", event_source)
        self.assertIn("er.async_get(hass).async_remove(entity_id)", sensor_source)
        self.assertIn("er.async_entries_for_config_entry", sensor_source)


if __name__ == "__main__":
    unittest.main()
