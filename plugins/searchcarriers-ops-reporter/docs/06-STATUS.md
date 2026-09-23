# Ops Reporter — Status

## Current state: 0.2.0 ready

Ops Reporter is implemented and validated. It retrieves current source data,
normalizes it, and produces Markdown, text, PDF, CSV, and JSON outputs for the
supported report tools.

- [x] MCP server and manifest
- [x] Carrier report, fleet report, comparison, and export handlers
- [x] Commands, embedded skill, and reporter agent
- [x] PDF rendering and field-mapping tests
- [x] Synthetic unit fixtures and opt-in live smoke tests
- [x] Repository and marketplace validation

## Known limits

- Reports are point-in-time decision aids and do not replace source verification.
- PDF output depends on the optional WeasyPrint runtime dependencies.
- API access and feature availability depend on the caller's SearchCarriers plan.

## Release history

| Version | Date | Changes |
|---|---|---|
| 0.2.0 | 2026-09-22 | v3 lookup migration, public-safe fixtures, Apache-2.0 release |
| 0.1.0 | 2026-02-26 | Initial implementation |
