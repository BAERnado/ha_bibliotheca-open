"""Regression check for persisted loan activity comparison."""

import importlib.util
from datetime import date
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
            "returned": {
                "copy_id": "returned",
                "title": "Old",
                "due_date": "2026-07-01",
            },
            "renewed": {
                "copy_id": "renewed",
                "title": "Kept",
                "due_date": "2026-07-02",
            },
        }
        current = {
            "borrowed": {
                "copy_id": "borrowed",
                "title": "New",
                "due_date": "2026-08-01",
                "renewable": True,
                "renewal_reason": None,
            },
            "renewed": {
                "copy_id": "renewed",
                "title": "Kept",
                "due_date": "2026-08-02",
                "renewable": False,
                "renewal_reason": "Too early",
            },
        }

        events, _ = ACTIVITY.activity_events(previous, current, date(2026, 7, 1))

        self.assertEqual({"borrowed", "returned", "renewed"}, {item[0] for item in events})
        returned = next(attributes for kind, attributes in events if kind == "returned")
        self.assertEqual("Old", returned["title"])
        renewed = next(attributes for kind, attributes in events if kind == "renewed")
        self.assertEqual("2026-07-02", renewed["previous_due_date"])
        self.assertEqual("2026-08-02", renewed["due_date"])

    def test_due_soon_is_emitted_once_per_due_date(self) -> None:
        current = {
            "copy": {
                "copy_id": "copy",
                "title": "Due",
                "due_date": "2026-07-22",
                "renewable": True,
                "renewal_reason": None,
            }
        }

        events, stored = ACTIVITY.activity_events(
            current, current, date(2026, 7, 19)
        )
        repeated, _ = ACTIVITY.activity_events(stored, current, date(2026, 7, 20))

        due_event = next(attributes for kind, attributes in events if kind == "due_soon")
        self.assertTrue(due_event["renewable"])
        self.assertFalse(any(kind == "due_soon" for kind, _ in repeated))


if __name__ == "__main__":
    unittest.main()
