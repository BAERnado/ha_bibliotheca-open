"""Pure comparison of active loan snapshots."""

from datetime import date, timedelta
from typing import Any

EVENT_BORROWED = "borrowed"
EVENT_RETURNED = "returned"
EVENT_RENEWED = "renewed"
EVENT_DUE_SOON = "due_soon"
EVENT_TYPES = [EVENT_BORROWED, EVENT_RETURNED, EVENT_RENEWED, EVENT_DUE_SOON]

LoanSnapshot = dict[str, dict[str, Any]]


def activity_events(
    previous: LoanSnapshot,
    current: LoanSnapshot,
    today: date,
    due_soon_days: int = 3,
) -> tuple[list[tuple[str, dict[str, Any]]], LoanSnapshot]:
    """Return lifecycle changes and a snapshot with notification markers."""

    current = {copy_id: dict(loan) for copy_id, loan in current.items()}
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
        events.append((EVENT_BORROWED, dict(current[copy_id])))
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

    latest_due = today + timedelta(days=due_soon_days)
    for copy_id, loan in current.items():
        due_date = date.fromisoformat(loan["due_date"])
        previous_marker = previous.get(copy_id, {}).get("due_soon_for")
        if today <= due_date <= latest_due and previous_marker != loan["due_date"]:
            events.append(
                (
                    EVENT_DUE_SOON,
                    {
                        "copy_id": copy_id,
                        "title": loan["title"],
                        "due_date": loan["due_date"],
                        "renewable": loan["renewable"],
                        "renewal_reason": loan["renewal_reason"],
                    },
                )
            )
            loan["due_soon_for"] = loan["due_date"]
        elif previous_marker == loan["due_date"]:
            loan["due_soon_for"] = previous_marker

    return events, current
