# Risk Engine — Status

## Current state: 0.3.0 ready

Risk Engine is implemented and validated. Current carrier lookup uses v3 search;
documented v1 authority, insurance, inspection, and out-of-service resources
supply the supporting evidence used by its analysis tools.

- [x] MCP server and manifest
- [x] Advisory score, v2 qualification reports, caller-policy vetting,
      insurance, and compliance handlers
- [x] Commands, embedded skill, and risk analyst agent
- [x] Synthetic unit fixtures and opt-in live smoke tests
- [x] Repository and marketplace validation

## Known limits

- Scores are decision support, not official safety ratings or legal conclusions.
- `vetting_check` requires a complete caller-owned policy. It has no hidden
  thresholds; `qualification_reports` preserves upstream named results.
- Missing API evidence is surfaced as missing or review-required; it is not
  silently treated as a pass.
- API access and feature availability depend on the caller's SearchCarriers plan.

## Release history

| Version | Date | Changes |
|---|---|---|
| 0.3.0 | 2026-09-23 | Added v2 named qualification reports and removed hidden vetting defaults |
| 0.2.0 | 2026-09-22 | v3 lookup migration, normalized inputs, sanitized public release |
| 0.1.0 | 2026-02-26 | Initial implementation |
