"""Constants for the Bibliotheca Open integration."""

from datetime import timedelta

DOMAIN = "bibliotheca_open"
PLATFORMS = ["calendar", "event", "sensor"]
DEFAULT_UPDATE_INTERVAL = timedelta(hours=1)

CONF_ACCOUNT_NAME = "account_name"
CONF_BASE_URL = "base_url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

SERVICE_RENEW_LOAN = "renew_loan"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_COPY_ID = "copy_id"
