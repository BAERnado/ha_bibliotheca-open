"""Checks for forgiving but bounded config-flow URL input."""

import importlib.util
from pathlib import Path
import unittest


PATH = Path(__file__).parents[1] / "custom_components" / "bibliotheca_open" / "url.py"
SPEC = importlib.util.spec_from_file_location("bibliotheca_url", PATH)
assert SPEC is not None and SPEC.loader is not None
URL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(URL)


class UrlTest(unittest.TestCase):
    def test_short_name_gets_official_host_and_https(self) -> None:
        self.assertEqual(
            "https://kaltenkirchen.bibliotheca-open.de",
            URL.normalize_base_url("kaltenkirchen"),
        )

    def test_official_host_gets_https(self) -> None:
        self.assertEqual(
            "https://kaltenkirchen.bibliotheca-open.de",
            URL.normalize_base_url("kaltenkirchen.bibliotheca-open.de/"),
        )

    def test_explicit_development_url_is_preserved(self) -> None:
        self.assertEqual(
            "http://localhost:8123",
            URL.normalize_base_url("http://localhost:8123"),
        )

    def test_other_bare_host_is_treated_as_a_subdomain(self) -> None:
        self.assertEqual(
            "https://example.com.bibliotheca-open.de",
            URL.normalize_base_url("example.com"),
        )

    def test_ambiguous_or_non_root_input_is_rejected(self) -> None:
        for value in ("https://example.com/path", "not valid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                URL.normalize_base_url(value)


if __name__ == "__main__":
    unittest.main()
