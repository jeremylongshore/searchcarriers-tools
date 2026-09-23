# Resumable Carrier Batch Runner decision playbook

## Operational problem

Large panels fail partially because of rate limits, bad identifiers, or tier errors; rerunning everything wastes quota and hides which records changed.

## Evidence contract

- Job: process a carrier panel with bounded concurrency, per-record receipts, and safe restart.
- API surface: GET /api/v1/export; GET /api/v3/company/{dot}; GET /api/v2/company/{dot}/qualification-reports.
- Required evidence: Input hash, run ID, per-DOT status, response source/as-of, attempts, error class, checkpoint, and final success/review/failure counts.
- Missing-data rule: Unknown DOTs and permanent 4xx errors stay in the manifest. A 429 or 5xx is retryable within a bounded budget.
- Decision boundary: Return COMPLETE, PARTIAL, or FAILED with a machine-readable error manifest; never discard successful rows because one carrier failed.
- Required follow-through: Resume from the checkpoint, then route completed evidence into qualification or export.

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

