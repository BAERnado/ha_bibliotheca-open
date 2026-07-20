"""Config flow for Bibliotheca Open."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from bibliotheca_open_client import BibliothecaClient
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import (
    CONF_ACCOUNT_NAME,
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)
from .url import normalize_base_url


class BibliothecaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one library account."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and store an account."""

        errors: dict[str, str] = {}
        if user_input is not None:
            account_name = user_input[CONF_ACCOUNT_NAME].strip()
            username = user_input[CONF_USERNAME].strip()
            if not account_name or not username or not user_input[CONF_PASSWORD]:
                errors["base"] = "missing_fields"
            try:
                base_url = normalize_base_url(user_input[CONF_BASE_URL])
            except ValueError:
                errors[CONF_BASE_URL] = "invalid_url"
            if not errors:
                client = BibliothecaClient(base_url)
                try:
                    login = await client.async_login(
                        username, user_input[CONF_PASSWORD]
                    )
                    if not login.authenticated:
                        errors["base"] = "invalid_auth"
                except Exception:
                    errors["base"] = "cannot_connect"
                finally:
                    await client.async_close()

            if not errors:
                unique_id = sha256(
                    f"{base_url.casefold()}\0{username}".encode()
                ).hexdigest()
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=account_name,
                    data={
                        CONF_ACCOUNT_NAME: account_name,
                        CONF_BASE_URL: base_url,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT_NAME): str,
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Start credential renewal after authentication expires."""

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and replace the password."""

        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            client = BibliothecaClient(entry.data[CONF_BASE_URL])
            try:
                login = await client.async_login(
                    entry.data[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                if login.authenticated:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                    )
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            finally:
                await client.async_close()

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )
