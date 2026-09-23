# Carrier Review Queue Digest decision playbook

## Operational problem

Daily summaries become misleading when they collapse missing evidence into passes or imply email delivery occurred.

## Evidence contract

- Job: turn supplied or fetched qualification results into a prioritized human review queue.
- API surface: GET /api/v2/company/{dot}/qualification-reports; Ops Reporter output.
- Required evidence: Qualification name, carrier, verdict, reasons, missing evidence, as-of, owner, and next action.
- Missing-data rule: Unavailable results remain unresolved and are excluded from pass counts.
- Decision boundary: Return DIGEST READY or INCOMPLETE with counts that reconcile to detail rows.
- Required follow-through: Assign Fail and Review items, then send through an explicitly configured delivery system.

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

