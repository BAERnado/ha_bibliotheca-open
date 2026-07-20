"""Normalize library installation input without Home Assistant dependencies."""

import re
from urllib.parse import urlsplit

_HOST_SUFFIX = ".bibliotheca-open.de"
_HOST_INPUT = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$",
    re.IGNORECASE,
)


def normalize_base_url(value: str) -> str:
    """Turn a short library name or host into an absolute root URL."""

    value = value.strip().rstrip("/")
    if "://" not in value:
        host = value.casefold()
        if host == "bibliotheca-open.de" or host.endswith(_HOST_SUFFIX):
            value = f"https://{host}"
        elif _HOST_INPUT.fullmatch(host):
            value = f"https://{host}{_HOST_SUFFIX}"
        else:
            raise ValueError("invalid library host or short name")

    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("absolute HTTP(S) root URL required")
    return value
