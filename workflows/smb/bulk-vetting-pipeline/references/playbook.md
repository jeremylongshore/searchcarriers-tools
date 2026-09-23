# Bulk Carrier Qualification Pipeline decision playbook

## Operational problem

A single bad row or rate limit should not invalidate hundreds of carrier decisions, and default criteria should not be invented.

## Evidence contract

- Job: run named policy qualification across a carrier list with restartable evidence.
- API surface: GET /api/v2/company/{dot}/qualification-reports; bulk_lookup; report/export tools.
- Required evidence: Run ID/input hash, qualification version, per-DOT verdict/evidence/as-of, attempts, errors, and reconciled totals.
- Missing-data rule: Invalid IDs and permanent errors enter review; transient errors retry within a bound.
- Decision boundary: Return COMPLETE, PARTIAL, or FAILED; missing evidence follows the named policy and never silently passes.
- Required follow-through: Resume failed rows, assign Review/Fail cases, and publish the evidence manifest with the output.

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

