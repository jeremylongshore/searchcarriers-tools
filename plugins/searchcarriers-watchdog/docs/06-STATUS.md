# Watchdog — Status

## Current state: 0.3.0 compatibility release

Watchdog implements the published v1 company-watch routes, current-state
compliance checks, and local formatting for Slack, Telegram, email, and webhook
payloads.

- [x] MCP server and manifest
- [x] Add, remove, and list watch operations
- [x] Current-state compliance evaluation
- [x] Format-only notification payloads
- [x] Commands, embedded skill, and monitor agent
- [x] Synthetic unit fixtures and opt-in live smoke tests
- [x] Repository and marketplace validation

## Known limits

- The published API does not expose the former assumed alert-feed route.
  `get_alerts` therefore returns a structured `endpoint_unavailable` response.
- `route_alert` formats caller-supplied events and never sends messages.
- The plugin does not claim historical compliance trend data.

## Release history

| Version | Date | Changes |
|---|---|---|
| 0.3.0 | 2026-09-23 | Pain-point skill rebuild, decision playbook, and behavioral eval specification |
| 0.2.0 | 2026-09-22 | Documented watch routes, truthful alert boundary, current-state checks |
| 0.1.0 | 2026-02-26 | Initial scaffold |
