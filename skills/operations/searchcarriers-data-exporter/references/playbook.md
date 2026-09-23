# Auditable Carrier Exporter decision playbook

## Operational problem

Exports lose field provenance, leak unnecessary contacts, or execute spreadsheet formulas when opened.

## Evidence contract

- Job: create a minimal, traceable carrier export that is safe to open and lawful to retain.
- API surface: GET /api/v1/export; GET /api/v3/company/{dot} with explicit fields.
- Required evidence: Selected fields, schema version, source routes, as-of, input hash, record count, errors, and retention/recipient note.
- Missing-data rule: Missing fields remain blank with a reason. 403 stops unsupported data; 429 resumes after Retry-After.
- Decision boundary: Return READY, PARTIAL, or BLOCKED with output path and manifest; never imply a partial export is complete.
- Required follow-through: Deliver through an approved internal channel and delete temporary API data under the organization retention policy.

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

