"""Pure comparison of active loan snapshots."""

from typing import Any

EVENT_BORROWED = "borrowed"
EVENT_RETURNED = "returned"
EVENT_RENEWED = "renewed"
EVENT_TYPES = [EVENT_BORROWED, EVENT_RETURNED, EVENT_RENEWED]


def activity_events(
    previous: dict[str, dict[str, str]],
    current: dict[str, dict[str, str]],
) -> list[tuple[str, dict[str, Any]]]:
    """Return borrowed, returned, and renewed changes."""

    events: list[tuple[str, dict[str, Any]]] = []
    for copy_id in previous.keys() - current.keys():
        loan = previous[copy_id]
        events.append(
            (
                EVENT_RETURNED,
                {
                    "copy_id": copy_id,
                    "title": loan["title"],
                    "previous_due_date": loan["due_date"],
                },
            )
        )
    for copy_id in current.keys() - previous.keys():
        events.append((EVENT_BORROWED, current[copy_id]))
    for copy_id in current.keys() & previous.keys():
        old = previous[copy_id]
        new = current[copy_id]
        if old["due_date"] != new["due_date"]:
            events.append(
                (
                    EVENT_RENEWED,
                    {
                        "copy_id": copy_id,
                        "title": new["title"],
                        "previous_due_date": old["due_date"],
                        "due_date": new["due_date"],
                    },
                )
            )
    return events
