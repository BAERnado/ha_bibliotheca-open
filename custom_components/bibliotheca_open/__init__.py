"""The Bibliotheca Open integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import ATTR_CONFIG_ENTRY_ID, ATTR_COPY_ID, DOMAIN, PLATFORMS, SERVICE_RENEW_LOAN
from .coordinator import BibliothecaCoordinator, create_client

BibliothecaConfigEntry = ConfigEntry[BibliothecaCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration and its account action."""

    async def async_renew_loan(call: ServiceCall) -> None:
        entry = hass.config_entries.async_get_entry(call.data[ATTR_CONFIG_ENTRY_ID])
        if entry is None or entry.domain != DOMAIN or not hasattr(entry, "runtime_data"):
            raise HomeAssistantError("Bibliotheca Open account is not loaded")
        try:
            await entry.runtime_data.async_renew_loan(call.data[ATTR_COPY_ID])
        except Exception as error:
            raise HomeAssistantError(str(error)) from error

    hass.services.async_register(
        DOMAIN,
        SERVICE_RENEW_LOAN,
        async_renew_loan,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
                vol.Required(ATTR_COPY_ID): cv.string,
            }
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BibliothecaConfigEntry) -> bool:
    """Set up one library account."""

    client = create_client(entry)
    coordinator = BibliothecaCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BibliothecaConfigEntry) -> bool:
    """Unload one library account."""

    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.client.async_close()
    return True
