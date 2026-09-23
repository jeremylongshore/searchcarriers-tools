# Carrier Intel — Status

## Current state: 0.3.0 ready

Carrier Intel is implemented and validated. Its four MCP tools use the current
hybrid SearchCarriers contract: v3 search/company/equipment plus the documented
v1 SCAC and VIN routes.

- [x] MCP server and manifest
- [x] `carrier_lookup`, `carrier_profile`, `entity_map`, and `fleet_summary`
- [x] Commands, embedded skill, and carrier analyst agent
- [x] Synthetic unit fixtures and opt-in live smoke tests
- [x] Repository and marketplace validation

## Known limits

- API access and feature availability depend on the caller's SearchCarriers plan.
- Live API responses are never committed; smoke receipts record structure only.
- Entity mapping follows available equipment VIN evidence and is not proof of
  corporate ownership or fraud.

## Release history

| Version | Date | Changes |
|---|---|---|
| 0.3.0 | 2026-09-23 | Pain-point skill rebuild, decision playbook, and behavioral eval specification |
| 0.2.0 | 2026-09-22 | Current API routing, shared normalization, sanitized public release |
| 0.1.0 | 2026-02-26 | Initial implementation |
