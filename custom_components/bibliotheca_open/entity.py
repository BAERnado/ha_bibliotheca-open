"""Shared Bibliotheca Open entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BibliothecaCoordinator


class BibliothecaEntity(CoordinatorEntity[BibliothecaCoordinator]):
    """Base entity for one library account."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BibliothecaCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="OCLC",
            model="Bibliotheca OPEN account",
        )
