"""Account updates for Bibliotheca Open."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from bibliotheca_open_client import AccountBalance, BibliothecaClient, Loan, RenewalResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AccountData:
    """Current account state."""

    loans: tuple[Loan, ...]
    balance: AccountBalance | None


class BibliothecaCoordinator(DataUpdateCoordinator[AccountData]):
    """Coordinate one library account."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: BibliothecaClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_UPDATE_INTERVAL,
            always_update=False,
        )
        self.entry = entry
        self.client = client
        self._request_lock = asyncio.Lock()

    async def _async_update_data(self) -> AccountData:
        async with self._request_lock:
            try:
                login = await self.client.async_login(
                    self.entry.data[CONF_USERNAME],
                    self.entry.data[CONF_PASSWORD],
                )
                if not login.authenticated:
                    raise ConfigEntryAuthFailed("Library credentials were rejected")
                loans = await self.client.async_fetch_loans(login.page)
                balance = await self.client.async_fetch_balance(login.page)
                return AccountData(loans=loans, balance=balance)
            except ConfigEntryAuthFailed:
                raise
            except Exception as error:
                raise UpdateFailed(f"Error updating library account: {error}") from error

    async def async_renew_loan(self, copy_id: str) -> RenewalResult:
        """Renew one loan and refresh all account entities."""

        async with self._request_lock:
            login = await self.client.async_login(
                self.entry.data[CONF_USERNAME],
                self.entry.data[CONF_PASSWORD],
            )
            if not login.authenticated:
                raise ConfigEntryAuthFailed("Library credentials were rejected")
            result = await self.client.async_renew_loan(copy_id)
        await self.async_request_refresh()
        return result


def create_client(entry: ConfigEntry) -> BibliothecaClient:
    """Create the cookie-compatible client owned by this config entry."""

    return BibliothecaClient(entry.data[CONF_BASE_URL])
