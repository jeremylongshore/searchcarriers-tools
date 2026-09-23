# Fleet Identity Reconciler decision playbook

## Operational problem

A truck at pickup may not match the approved carrier, while leased or transferred equipment can create legitimate multi-carrier history.

## Evidence contract

- Job: reconcile a VIN, the carrier claiming it, and the companies observed operating it.
- API surface: GET /api/v1/search/by-vin/{vin}; GET /api/v3/company/{dot}/equipment.
- Required evidence: VIN, claimed DOT, observed DOT records, equipment details, inspection dates where returned, and exact match/mismatch status.
- Missing-data rule: A VIN with no result is unresolved; malformed VINs stop before the API call.
- Decision boundary: Return MATCH, MISMATCH, MULTIPLE OBSERVED CARRIERS, or INSUFFICIENT EVIDENCE.
- Required follow-through: For a mismatch, stop tendering and verify truck, trailer, plate, driver, and dispatch through the original trusted contact.

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

