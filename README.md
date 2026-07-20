# Bibliotheca Open for Home Assistant

HACS-installable Home Assistant custom integration for library accounts using
[bibliotheca-open.de](https://bibliotheca-open.de/).

## Features

- UI configuration with one config entry per library account
- multiple people, accounts, and library installations
- configurable polling per account, defaulting to 60 minutes
- one date sensor per currently borrowed medium
- aggregate loan and account-balance sensors
- one due-date calendar per account
- persisted loan lifecycle events
- explicit action for renewing one loan

## Installation

Until the first PyPI release, the integration installs the client directly
from the pinned Git commit `2c970aa`. Home Assistant therefore needs outbound
access to GitHub while installing the dependency.

Add this repository to HACS as a custom **Integration** repository, install it,
and restart Home Assistant. Then add **Bibliotheca Open** through
**Settings → Devices & services**.

Each configured account needs:

- a freely chosen account name;
- the installation root URL or short subdomain, for example
  `https://kaltenkirchen.bibliotheca-open.de`,
  `kaltenkirchen.bibliotheca-open.de`, or just `kaltenkirchen`;
- library card number and password.

## Update behavior and polling interval

The account defaults to an update every 60 minutes and is refreshed immediately
after a renewal action. If its session expired, the integration logs in again
with the stored credentials.

Change the interval under **Settings → Devices & services → Bibliotheca Open →
Configure**. Values from 15 to 1440 minutes are accepted. With several accounts
at the same library, choose slightly different intervals, for example 57, 63,
and 71 minutes. This spreads later polls; the initial setup check still runs
immediately for each account.

Returned media disappear from the current Home Assistant state. The integration
does not maintain a second lending-history database; lifecycle events are kept
according to the Home Assistant Recorder retention settings. A detected return
time means that an update first noticed the missing loan. It can therefore be
up to one polling interval later than the actual return.

## Device and entities

Each config entry creates one Home Assistant device named after the configured
account. Home Assistant derives entity IDs from the account, entity name, and
optionally its area. The integration deliberately does not force its domain
into entity IDs. Examples below are placeholders; use the IDs shown by your
Home Assistant instance.

### Account sensors

| Entity name | State | Additional attributes |
| --- | --- | --- |
| Loans | Number of active loans | — |
| Overdue loans | Number whose due date passed | — |
| Renewable loans | Number currently renewable | — |
| Balance | Complete account balance | `open_fees`, `deposits` |

The balance is unavailable if the library installation does not expose a fee
summary.

### Loan sensors

Every active loan is represented by a date sensor. Its state is the current due
date. It provides these attributes:

| Attribute | Meaning |
| --- | --- |
| `config_entry_id` | Account identifier used by renewal actions |
| `copy_id` | Copy identifier required for renewal |
| `author` | Author, if supplied by OPEN |
| `media_group` | Media group such as book, game, or Tonie |
| `overdue` | Whether the due date has passed |
| `renewable` | Current server decision: `true`, `false`, or unavailable |
| `renewal_reason` | Server explanation when renewal is unavailable |
| `renewal_delay` | Additional server timing information |
| `renewal_text` | Server text describing the offered renewal |

Do not group loans by generated entity names. They remain discoverable even
after renaming or area changes:

```jinja
{% for entity_id in integration_entities('bibliotheca_open') %}
  {% if entity_id.startswith('sensor.')
        and state_attr(entity_id, 'copy_id') is not none %}
    {{ entity_id }}: renewable={{ state_attr(entity_id, 'renewable') }}
  {% endif %}
{% endfor %}
```

### Due-date calendar

Each account has one read-only calendar named **Due dates**. Every active loan
is an all-day event on its due date. The event summary is the title; its
description contains the copy ID, current renewability, and a possible server
reason.

Use calendar triggers instead of the calendar entity's current state. Calendar
triggers handle every loan, including several media due on the same day.

### Loan activity event entity

Each account has one **Loan activity** event entity. Its state is the timestamp
of the latest event. `event_type` identifies the event, and the remaining
attributes describe the affected loan.

| Event type | When emitted | Attributes in addition to `config_entry_id` |
| --- | --- | --- |
| `borrowed` | A new copy appears | `copy_id`, `title`, `due_date`, `renewable`, `renewal_reason` |
| `returned` | A previously active copy disappears | `copy_id`, `title`, `previous_due_date` |
| `renewed` | The due date changes | `copy_id`, `title`, `previous_due_date`, `due_date` |
| `due_soon` | A copy enters the final three days before its due date | `copy_id`, `title`, `due_date`, `renewable`, `renewal_reason` |

`due_soon` is emitted once per due date. After a successful renewal it can be
emitted again when the new date enters the three-day window. The stored activity
snapshot survives Home Assistant restarts. The first snapshot does not create
artificial `borrowed` events, but it does report loans already due soon.

## Action: renew a loan

`bibliotheca_open.renew_loan` renews exactly one copy immediately. There is no
confirmation step on the library website.

| Field | Meaning |
| --- | --- |
| `config_entry_id` | Home Assistant config-entry ID of the account |
| `copy_id` | Copy ID exposed by the loan sensor or activity event |

The client refreshes the account and refuses the operation unless OPEN still
reports that copy as renewable. All account entities are refreshed afterwards.
In the visual action editor, the account field provides a config-entry selector.

## Automation: notify two days before a due date

Replace the calendar entity ID with the one created for your account. This
creates a persistent Home Assistant notification two days before every due
date. `parallel` allows several media with the same due date to trigger.

```yaml
alias: "Library: loan due in two days"
triggers:
  - trigger: calendar.event_started
    target:
      entity_id: calendar.my_library_due_dates
    options:
      offset:
        days: 2
      offset_type: before
actions:
  - action: persistent_notification.create
    data:
      title: "Library loan due in two days"
      message: >-
        {{ trigger.calendar_event.summary }} is due on
        {{ trigger.calendar_event.start }}.
mode: parallel
```

## Automation: renew two or more loans

This example attempts several renewals sequentially every morning. Replace the
config-entry ID and copy IDs with values from your account and loan entities.
Each successful call changes the library account immediately. A rejected copy
does not stop the remaining attempts because `continue_on_error` is enabled.

```yaml
alias: "Library: renew selected loans"
triggers:
  - trigger: time
    at: "06:00:00"
actions:
  - repeat:
      for_each:
        - "COPY_ID_FIRST_LOAN"
        - "COPY_ID_SECOND_LOAN"
        - "COPY_ID_OPTIONAL_THIRD_LOAN"
      sequence:
        - action: bibliotheca_open.renew_loan
          continue_on_error: true
          data:
            config_entry_id: "HOME_ASSISTANT_CONFIG_ENTRY_ID"
            copy_id: "{{ repeat.item }}"
mode: single
```

For unattended renewal, add conditions appropriate to your household. In
particular, inspect the loan's `renewable` state or use the structured
`due_soon` event before invoking a mutating action.

## Automation: renew everything due tomorrow and report the result

The following account-specific automation runs one day before a calendar due
date. It collects every loan of that account due on the same date, renews those
currently marked renewable, and sends one summary after all renewal calls
succeed. Replace the calendar entity and config-entry ID.

`mode: single` is intentional: when several all-day events start together, the
first run handles every loan for that date while duplicate triggers are ignored.

```yaml
alias: "Library: renew loans due tomorrow"
triggers:
  - trigger: calendar.event_started
    target:
      entity_id: calendar.my_library_due_dates
    options:
      offset:
        days: 1
      offset_type: before
variables:
  account_config_entry_id: "HOME_ASSISTANT_CONFIG_ENTRY_ID"
  target_due_date: "{{ (trigger.calendar_event.start|string)[:10] }}"
  renewable_copy_ids: >-
    {% set ns = namespace(items=[]) %}
    {% for entity_id in integration_entities('bibliotheca_open') %}
      {% if entity_id.startswith('sensor.')
            and state_attr(entity_id, 'config_entry_id') == account_config_entry_id
            and states(entity_id) == target_due_date
            and state_attr(entity_id, 'renewable') is true %}
        {% set ns.items = ns.items + [state_attr(entity_id, 'copy_id')] %}
      {% endif %}
    {% endfor %}
    {{ ns.items }}
  renewed_titles: >-
    {% set ns = namespace(items=[]) %}
    {% for entity_id in integration_entities('bibliotheca_open') %}
      {% if entity_id.startswith('sensor.')
            and state_attr(entity_id, 'config_entry_id') == account_config_entry_id
            and states(entity_id) == target_due_date
            and state_attr(entity_id, 'renewable') is true %}
        {% set ns.items = ns.items + [state_attr(entity_id, 'friendly_name')] %}
      {% endif %}
    {% endfor %}
    {{ ns.items }}
  return_titles: >-
    {% set ns = namespace(items=[]) %}
    {% for entity_id in integration_entities('bibliotheca_open') %}
      {% if entity_id.startswith('sensor.')
            and state_attr(entity_id, 'config_entry_id') == account_config_entry_id
            and states(entity_id) == target_due_date
            and state_attr(entity_id, 'renewable') is false %}
        {% set reason = state_attr(entity_id, 'renewal_reason') or 'no reason supplied' %}
        {% set item = state_attr(entity_id, 'friendly_name') ~ ': ' ~ reason %}
        {% set ns.items = ns.items + [item] %}
      {% endif %}
    {% endfor %}
    {{ ns.items }}
actions:
  - repeat:
      for_each: "{{ renewable_copy_ids }}"
      sequence:
        - action: bibliotheca_open.renew_loan
          data:
            config_entry_id: "{{ account_config_entry_id }}"
            copy_id: "{{ repeat.item }}"
  - action: notify.persistent_notification
    data:
      title: "Library renewal result"
      message: >-
        Renewed:
        {% if renewed_titles %}
        - {{ renewed_titles | join('\n- ') }}
        {% else %}
        - none
        {% endif %}

        Not renewed; check or return:
        {% if return_titles %}
        - {{ return_titles | join('\n- ') }}
        {% else %}
        - none
        {% endif %}
mode: single
```

The server only exposes `renewable` and a localized reason. A negative decision
does not always mean that return is absolutely required: it can also be a
temporary restriction caused by the library's renewal-date calculation. The
notification therefore includes the original reason instead of guessing. If a
renewal call fails unexpectedly, Home Assistant stops the sequence and records
the failure in the automation trace rather than falsely reporting success.

## License

Copyright 2026 BAERnado. Licensed under the
[Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution information.

## Development disclosure

This project was developed predominantly with AI-assisted *vibe coding*. The
project owner directed the requirements, supplied live observations, performed
functional tests, and reviewed parts of the source code, but did not manually
write or comprehensively audit every implementation detail. Users and
contributors should therefore review and test the integration appropriately
for their own Home Assistant environment, especially before enabling
automations that renew loans without manual confirmation.
