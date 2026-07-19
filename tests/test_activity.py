"""Regression check for persisted loan activity comparison."""

import importlib.util
from pathlib import Path
import unittest


PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "bibliotheca_open"
    / "activity.py"
)
SPEC = importlib.util.spec_from_file_location("bibliotheca_activity", PATH)
assert SPEC is not None and SPEC.loader is not None
ACTIVITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACTIVITY)


class ActivityTest(unittest.TestCase):
    def test_borrowed_returned_and_renewed(self) -> None:
        previous = {
            "returned": {"copy_id": "returned", "title": "Old", "due_date": "2026-07-01"},
            "renewed": {"copy_id": "renewed", "title": "Kept", "due_date": "2026-07-02"},
        }
        current = {
            "borrowed": {"copy_id": "borrowed", "title": "New", "due_date": "2026-08-01"},
            "renewed": {"copy_id": "renewed", "title": "Kept", "due_date": "2026-08-02"},
        }

        events = ACTIVITY.activity_events(previous, current)

        self.assertEqual({"borrowed", "returned", "renewed"}, {item[0] for item in events})
        returned = next(attributes for kind, attributes in events if kind == "returned")
        self.assertEqual("Old", returned["title"])
        renewed = next(attributes for kind, attributes in events if kind == "renewed")
        self.assertEqual("2026-07-02", renewed["previous_due_date"])
        self.assertEqual("2026-08-02", renewed["due_date"])


if __name__ == "__main__":
    unittest.main()
