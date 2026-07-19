"""Loan activity events for Bibliotheca Open."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify

from .activity import EVENT_TYPES, activity_events
from .const import DOMAIN
from .coordinator import BibliothecaCoordinator
from .entity import BibliothecaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BibliothecaCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one persisted loan activity entity."""

    async_add_entities([LoanActivityEvent(entry.runtime_data)])


class LoanActivityEvent(BibliothecaEntity, EventEntity):
    """Report changes between successful account updates."""

    _attr_event_types = EVENT_TYPES
    _attr_name = "Loan activity"

    def __init__(self, coordinator: BibliothecaCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_loan_activity"
        self._attr_suggested_object_id = (
            f"bibliotheca_open_{slugify(coordinator.entry.title)}_loan_activity"
        )
        self._store = Store[dict[str, dict[str, Any]]](
            coordinator.hass,
            1,
            f"{DOMAIN}.{coordinator.entry.entry_id}.active_loans",
        )
        self._known: dict[str, dict[str, Any]] | None = None
        self._process_lock = asyncio.Lock()

    async def async_added_to_hass(self) -> None:
        """Restore the last successful snapshot and start tracking changes."""

        await super().async_added_to_hass()
        self._known = await self._store.async_load()
        await self._async_process_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Compare the new account snapshot without blocking the callback."""

        self.hass.async_create_task(self._async_process_update())

    def _current(self) -> dict[str, dict[str, Any]]:
        return {
            loan.copy_id: {
                "copy_id": loan.copy_id,
                "title": loan.title,
                "due_date": loan.due_date.isoformat(),
                "renewable": loan.renewal.renewable if loan.renewal else None,
                "renewal_reason": loan.renewal.reason if loan.renewal else None,
            }
            for loan in self.coordinator.data.loans
        }

    async def _async_process_update(self) -> None:
        async with self._process_lock:
            current = self._current()
            if self._known is None:
                # Establish a lifecycle baseline but still report loans already
                # inside the due-soon window.
                previous = current
            else:
                previous = self._known

            events, current = activity_events(previous, current, date.today())
            for event_type, attributes in events:
                attributes["config_entry_id"] = self.coordinator.entry.entry_id
                self._trigger_event(event_type, attributes)

            self._known = current
            await self._store.async_save(current)
