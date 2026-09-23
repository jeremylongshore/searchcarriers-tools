# TMS Reconciliation Planner decision playbook

## Operational problem

Blind TMS overwrites destroy local fields, duplicate carriers, and turn stale API data into operational status.

## Evidence contract

- Job: produce a dry-run carrier change set with idempotent keys and rollback evidence.
- API surface: GET /api/v3/company/{dot}; GET /api/v2/company/{dot}/qualification-reports; local TMS adapter.
- Required evidence: Run ID, DOT key, source/as-of, before/after diff, protected fields, conflict reason, action, result, and rollback reference.
- Missing-data rule: Ambiguous DOTs, missing required evidence, or a stale snapshot become conflicts; never auto-create from a name match.
- Decision boundary: Return NO CHANGE, PROPOSED, APPLIED, PARTIAL, or ROLLED BACK per record.
- Required follow-through: Review the dry run, apply approved changes, reconcile reads after writes, and preserve rollback receipts.

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

