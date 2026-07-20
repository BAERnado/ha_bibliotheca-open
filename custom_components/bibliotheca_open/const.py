"""Constants for the Bibliotheca Open integration."""

DOMAIN = "bibliotheca_open"
PLATFORMS = ["calendar", "event", "sensor"]
DEFAULT_UPDATE_INTERVAL_MINUTES = 60
MIN_UPDATE_INTERVAL_MINUTES = 15
MAX_UPDATE_INTERVAL_MINUTES = 1440

CONF_ACCOUNT_NAME = "account_name"
CONF_BASE_URL = "base_url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_UPDATE_INTERVAL = "update_interval"

SERVICE_RENEW_LOAN = "renew_loan"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_COPY_ID = "copy_id"
