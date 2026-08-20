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
        self.assertEqual("0.5.0", manifest["version"])
        self.assertTrue((COMPONENT / "button.py").is_file())
        self.assertTrue((COMPONENT / "event.py").is_file())
        self.assertEqual(
            [
                "bibliotheca-open-client@git+https://github.com/BAERnado/"
                "bibliotheca-open-client.git@53df917"
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
        self.assertIn('registry_entry.domain == "sensor"', sensor_source)

    def test_rejected_renewals_are_reported(self) -> None:
        setup_source = (COMPONENT / "__init__.py").read_text()
        coordinator_source = (COMPONENT / "coordinator.py").read_text()

        self.assertIn('_LOGGER.exception("Loan renewal failed")', setup_source)
        self.assertIn("if not result.renewed:", coordinator_source)

    def test_renewal_button_is_guarded_and_cleans_up(self) -> None:
        button_source = (COMPONENT / "button.py").read_text()

        self.assertIn("and loan.renewal.renewable", button_source)
        self.assertIn("await self.coordinator.async_renew_loan", button_source)
        self.assertIn('registry_entry.domain == "button"', button_source)


if __name__ == "__main__":
    unittest.main()
