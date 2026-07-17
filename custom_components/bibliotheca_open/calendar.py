"""Due-date calendar for Bibliotheca Open."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BibliothecaCoordinator
from .entity import BibliothecaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BibliothecaCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one due-date calendar."""

    async_add_entities([BibliothecaCalendar(entry.runtime_data)])


class BibliothecaCalendar(BibliothecaEntity, CalendarEntity):
    """Calendar containing one all-day event per active loan."""

    _attr_name = "Due dates"

    def __init__(self, coordinator: BibliothecaCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_due_dates"

    def _events(self) -> list[CalendarEvent]:
        events = []
        for loan in self.coordinator.data.loans:
            renewal = loan.renewal
            details = [f"Copy ID: {loan.copy_id}"]
            if renewal is not None:
                details.append(f"Renewable: {'yes' if renewal.renewable else 'no'}")
                if renewal.reason:
                    details.append(renewal.reason)
            events.append(
                CalendarEvent(
                    summary=loan.title,
                    start=loan.due_date,
                    end=loan.due_date + timedelta(days=1),
                    description="\n".join(details),
                )
            )
        return sorted(events, key=lambda event: event.start)

    @property
    def event(self) -> CalendarEvent | None:
        today = date.today()
        return next((event for event in self._events() if event.end > today), None)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return due dates overlapping the requested range."""

        start = start_date.date()
        end = end_date.date()
        return [event for event in self._events() if event.start < end and event.end > start]
