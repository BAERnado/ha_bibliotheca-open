# Bibliotheca Open for Home Assistant

HACS-installable Home Assistant custom integration for library accounts using
[bibliotheca-open.de](https://bibliotheca-open.de/).

## Features

- UI configuration with one config entry per library account
- multiple people, accounts, and library installations
- hourly polling with automatic login after an expired session
- one date sensor per currently borrowed medium
- loan title, author, media group, copy ID, overdue and renewal information
- account sensors for active, overdue, and renewable loans
- monetary account balance with fee and deposit attributes
- one due-date calendar per account
- explicit `bibliotheca_open.renew_loan` action

Returned media are removed from Home Assistant's current state. The integration
does not maintain a separate lending history; Home Assistant's Recorder can
retain the previous entity history according to the user's Recorder settings.

## Installation

Until the first PyPI release, the integration installs the client directly
from the pinned Git commit `d81cf1d`. This requires outbound access from Home
Assistant to GitHub during dependency installation. Replace the Git requirement
with an exact PyPI version after publishing the package.

For development, copy `custom_components/bibliotheca_open` into the
`custom_components` directory of a Home Assistant development configuration,
restart Home Assistant, then add **Bibliotheca Open** through
**Settings → Devices & services**.

Enter:

- a freely chosen account name;
- the installation root URL, for example
  `https://kaltenkirchen.bibliotheca-open.de`;
- library card number and password.

## Renewal action

`bibliotheca_open.renew_loan` changes the library account immediately. It needs
the Home Assistant config-entry ID and the `copy_id` attribute of a loan sensor.
The integration refreshes all account entities after the request. Automatic
renewal is intentionally left to a Home Assistant automation so users can add
their own timing, notification, and safety conditions.
