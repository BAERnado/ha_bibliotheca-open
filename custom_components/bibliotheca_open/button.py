"""Renewal buttons for active Bibliotheca Open loans."""

from __future__ import annotations

from bibliotheca_open_client import Loan
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BibliothecaCoordinator
from .entity import BibliothecaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BibliothecaCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one renewal button per active loan."""

    coordinator = entry.runtime_data
    buttons: dict[str, RenewalButton] = {}

    async def remove_button(button: RenewalButton) -> None:
        entity_id = button.entity_id
        await button.async_remove()
        if entity_id is not None:
            er.async_get(hass).async_remove(entity_id)

    @callback
    def sync_buttons() -> None:
        current = {loan.copy_id for loan in coordinator.data.loans}
        removing_entity_ids: set[str] = set()
        for copy_id in set(buttons) - current:
            button = buttons.pop(copy_id)
            if button.entity_id is not None:
                removing_entity_ids.add(button.entity_id)
            hass.async_create_task(remove_button(button))

        additions = [
            buttons.setdefault(copy_id, RenewalButton(coordinator, copy_id))
            for copy_id in current - buttons.keys()
        ]
        if additions:
            async_add_entities(additions)

        registry = er.async_get(hass)
        active_unique_ids = {
            f"{entry.entry_id}_renew_{copy_id}" for copy_id in current
        }
        for registry_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        ):
            if (
                registry_entry.domain == "button"
                and registry_entry.unique_id.startswith(f"{entry.entry_id}_renew_")
                and registry_entry.unique_id not in active_unique_ids
                and registry_entry.entity_id not in removing_entity_ids
            ):
                hass.states.async_remove(registry_entry.entity_id)
                registry.async_remove(registry_entry.entity_id)

    sync_buttons()
    entry.async_on_unload(coordinator.async_add_listener(sync_buttons))


class RenewalButton(BibliothecaEntity, ButtonEntity):
    """Immediately renew one currently renewable loan."""

    _attr_icon = "mdi:book-refresh"

    def __init__(self, coordinator: BibliothecaCoordinator, copy_id: str) -> None:
        super().__init__(coordinator)
        self.copy_id = copy_id
        self._attr_unique_id = f"{coordinator.entry.entry_id}_renew_{copy_id}"

    @property
    def loan(self) -> Loan | None:
        return next(
            (loan for loan in self.coordinator.data.loans if loan.copy_id == self.copy_id),
            None,
        )

    @property
    def name(self) -> str:
        return f"Renew {self.loan.title}" if self.loan else "Renew loan"

    @property
    def available(self) -> bool:
        loan = self.loan
        return (
            super().available
            and loan is not None
            and loan.renewal is not None
            and loan.renewal.renewable
        )

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        loan = self.loan
        return {
            "copy_id": self.copy_id,
            "renewal_reason": (
                loan.renewal.reason if loan and loan.renewal else None
            ),
        }

    async def async_press(self) -> None:
        """Renew the loan and refresh the account."""

        await self.coordinator.async_renew_loan(self.copy_id)
