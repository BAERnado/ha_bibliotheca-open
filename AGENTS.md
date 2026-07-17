# AGENTS.md

## Ponytail, lazy senior dev mode

Be efficient, not careless. Before writing code, stop at the first solution that
holds: avoid building it, use the standard library, use a native Home Assistant
feature, use an already-installed dependency, or write the minimum code that
works.

- No unrequested abstractions, dependencies, or boilerplate.
- Prefer deletion over addition and boring code over clever code.
- Choose the edge-case-correct option when alternatives are equally small.
- Mark intentional shortcuts with a `ponytail:` comment naming the ceiling and
  upgrade path.
- Do not compromise input validation at trust boundaries, data-loss prevention,
  security, accessibility, logging, or explicitly requested behavior.
- Non-trivial logic needs one small runnable check that fails when it breaks.
  Trivial one-liners need no test.

## Repository purpose

This repository contains the HACS-installable Home Assistant custom component
for bibliotheca-open.de accounts. It supports multiple people, multiple library
accounts per person, and libraries other than the currently known Kaltenkirchen
installation.

The integration is responsible for:

- config flows and storage of credentials and server addresses;
- Home Assistant entities, calendars, and events;
- due dates and renewal information;
- Home Assistant actions such as requesting a renewal through the client;
- useful diagnostic logging without exposing credentials or personal data.

The integration is not responsible for logging in to library websites, parsing
HTML, interpreting website state, or performing renewal HTTP requests. Those
belong in the separately packaged `bibliotheca-open-client` dependency. Do not
duplicate scraper behavior here.

## Home Assistant constraints

- Use Home Assistant native APIs and established integration patterns first.
- Keep blocking network and parser work outside Home Assistant's event loop.
- Treat credentials, account identifiers, borrowed-item data, and server
  responses as sensitive; never include them unredacted in logs.
- Keep the component installable through HACS and declare runtime dependencies
  in `custom_components/bibliotheca_open/manifest.json` only when needed.
- The client is a library dependency, not a dedicated service or daemon.

## Environment and delivery

Home Assistant will pull this component and users may provide logs through chat
or files. Add meaningful diagnostics for failures likely to occur only in that
environment. If an efficient and correct check needs a missing host package,
ask the user to install it for their operating system.

Completed development work must be committed meaningfully and pushed to
`origin/master`. The remote repository must remain on GitHub.
