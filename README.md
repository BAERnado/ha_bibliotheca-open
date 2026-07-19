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
- one Recorder-backed loan activity entity with `borrowed`, `returned`, and
  `renewed` events
- one `due_soon` event when a loan enters the final three days before its due
  date, including copy ID and current renewal status
- explicit `bibliotheca_open.renew_loan` action

Returned media are removed from Home Assistant's current state. The integration
does not maintain a separate lending history; Home Assistant's Recorder can
retain the previous entity history according to the user's Recorder settings.
The return time is when an hourly update first notices that a copy disappeared,
not necessarily the exact time it was handed back at the library.

New sensor IDs are suggested as
`sensor.bibliotheca_open_<account>_<medium>_<copy_id>`. Existing entity IDs are
not renamed automatically by Home Assistant. Automations should select loan
sensors by their `copy_id` attribute rather than relying on generated names.

All loan sensors can be selected in a template independently of their names:

```jinja
{% for entity_id in integration_entities('bibliotheca_open') %}
  {% if entity_id.startswith('sensor.')
        and state_attr(entity_id, 'copy_id') is not none %}
    {{ entity_id }}: {{ state_attr(entity_id, 'renewable') }}
  {% endif %}
{% endfor %}
```

Use the due-date calendar with an offset for ordinary reminders. For structured
automation, trigger on any state change of the account's loan-activity event
entity and select `due_soon`:

```yaml
triggers:
  - trigger: state
    entity_id: event.bibliotheca_open_my_account_loan_activity
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.attributes.event_type == 'due_soon' }}"
actions:
  - action: persistent_notification.create
    data:
      title: "Library loan due soon"
      message: >-
        {{ trigger.to_state.attributes.title }} is due on
        {{ trigger.to_state.attributes.due_date }}.
mode: queued
```

The event attributes also expose `config_entry_id`, `copy_id`, `renewable`, and
`renewal_reason`, so an automation can add its own conditions before calling
`renew_loan` without parsing entity names or calendar descriptions.

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
