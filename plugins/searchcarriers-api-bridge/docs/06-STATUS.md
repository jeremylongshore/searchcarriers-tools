# API Bridge — Status

## Current state: 0.3.0 ready

API Bridge is implemented and validated. It provides hybrid-version health
checks, bounded bulk lookup, TMS mapping, and local downstream webhook
configuration.

- [x] MCP server and manifest
- [x] `api_health`, `bulk_lookup`, `tms_sync`, and `webhook_manage`
- [x] v3 search plus documented v1 detail resources
- [x] Commands, embedded skill, and integration manager agent
- [x] Synthetic unit fixtures and opt-in live smoke tests
- [x] Repository and marketplace validation

## Known limits

- `webhook_manage` stores local downstream configuration; it does not create
  SearchCarriers webhooks because no such public CRUD route is documented.
- Bulk operations are bounded and respect the caller's plan and rate limits.
- Live response data is not stored in this repository.

## Release history

| Version | Date | Changes |
|---|---|---|
| 0.3.0 | 2026-09-23 | Pain-point skill rebuild, decision playbook, and behavioral eval specification |
| 0.2.0 | 2026-09-22 | Hybrid health probes, v3 lookup migration, public-safe release |
| 0.1.0 | 2026-02-26 | Initial implementation |
