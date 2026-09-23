# Carrier Integration Operator decision playbook

## Operational problem

Integration failures become silent data drift when health, partial success, local webhook ownership, and rollback are not explicit.

## Evidence contract

- Job: run API health, resumable bulk lookup, dry-run TMS reconciliation, and local downstream webhook configuration.
- API surface: MCP tools: api_health, bulk_lookup, tms_sync, webhook_manage.
- Required evidence: Route health without records, batch run receipts, TMS diff/result, local webhook configuration path, errors, and rollback evidence.
- Missing-data rule: 403 means tier/access; 429 honors Retry-After; partial runs retain successful records and an error manifest.
- Decision boundary: Return HEALTHY/DEGRADED, COMPLETE/PARTIAL, or PROPOSED/APPLIED with exact scope.
- Required follow-through: Retry only transient failures, review TMS conflicts, and test downstream delivery separately.

## Guardrails

1. Resolve identity before evaluating the record.
2. Keep observed API facts separate from policy and inference.
3. Never turn absent data into zero, false, safe, or fraudulent.
4. Never describe SearchCarriers data as an official FMCSA safety rating or guarantee.
5. Never use this service for employment, credit, insurance, housing, or another FCRA-regulated eligibility decision.
6. Keep API results inside the licensed organization and retain only what the workflow needs.

## Review checklist

- [ ] Identifier and legal entity agree.
- [ ] Route and parameter names match the repository API contract.
- [ ] Evidence has an as-of date and source.
- [ ] The intended operation and named policy are explicit.
- [ ] Unknowns and partial failures are visible.
- [ ] The status uses only this skill's bounded vocabulary.
- [ ] A human-owned next action is present.

## Sources

- [SearchCarriers API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md) — versioned routes, authentication, parameters, and data handling.
- [SearchCarriers API documentation](https://searchcarriers.com/docs/api) — published endpoint contract.
- [SearchCarriers terms](https://searchcarriers.com/terms-of-service) — internal-use and decision limits.
- [FMCSA fraud and identity-theft guidance](https://www.fmcsa.dot.gov/mission/help/broker-and-carrier-fraud-and-identity-theft) — independent verification practices.
- [FMCSA insurance requirements](https://www.fmcsa.dot.gov/registration/insurance-filing-requirements) — requirements depend on operation.

