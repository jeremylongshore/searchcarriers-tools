# Carrier Panel Compliance Dashboard decision playbook

## Operational problem

A green dashboard can hide old snapshots, low-exposure carriers, and failed API calls.

## Evidence contract

- Job: build an as-of panel dashboard that exposes stale, missing, and high-priority evidence.
- API surface: GET /api/v3/company/{dot}; GET /api/v2/company/{dot}/qualification-reports; company watch routes.
- Required evidence: Panel input hash, run/as-of, per-carrier evidence status, qualification, watch state, errors, and aging.
- Missing-data rule: Missing or old snapshots appear in a dedicated queue and do not count as compliant.
- Decision boundary: Return CURRENT, PARTIAL, or STALE; collection failure is never green.
- Required follow-through: Refresh failed/stale rows and assign policy reviews before relying on the dashboard.

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

