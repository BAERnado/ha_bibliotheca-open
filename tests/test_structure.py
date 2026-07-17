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
        self.assertEqual(
            [
                "bibliotheca-open-client@git+https://github.com/BAERnado/"
                "bibliotheca-open-client.git@d81cf1d"
            ],
            manifest["requirements"],
        )
        for language in ("de", "en"):
            translation = json.loads(
                (COMPONENT / "translations" / f"{language}.json").read_text()
            )
            self.assertIn("renew_loan", translation["services"])


if __name__ == "__main__":
    unittest.main()
