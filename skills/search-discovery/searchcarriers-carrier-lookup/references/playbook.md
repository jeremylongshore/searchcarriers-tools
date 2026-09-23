# Carrier Candidate Finder decision playbook

## Operational problem

A name-only search returns false matches, while a broad search returns candidates that cannot serve the load.

## Evidence contract

- Job: find a defensible carrier shortlist for a named company, identifier, geography, fleet need, insurance requirement, or lane.
- API surface: GET /api/v3/search; GET /api/v1/search/scac; GET /api/v1/search/by-vin/{vin}.
- Required evidence: DOT/docket identity, legal name, location, fleet facts, selected filters, pagination metadata, and an as-of timestamp.
- Missing-data rule: An empty page means no candidates under those filters. A missing field is unknown, never false or zero.
- Decision boundary: Return MATCH, POSSIBLE MATCH, or NO MATCH for identity; for sourcing return a ranked candidate list without calling it approved.
- Required follow-through: Resolve ambiguous identities, open the selected carrier profile, then run authority, insurance, and policy qualification checks.

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

