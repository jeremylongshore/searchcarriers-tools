# Operating Authority Verifier decision playbook

## Operational problem

A valid DOT is not the same as active for-hire authority, and similar names or old dockets cause misidentification.

## Evidence contract

- Job: verify that the identified entity has the authority required for the intended job.
- API surface: GET /api/v3/company/{dot}?fields=authorities,operation,insurance; GET /api/v1/authority/{docketNumber}/history.
- Required evidence: Legal identity, DOT/docket, required role, current authority type/status, history events, insurance linkage, and as-of timestamp.
- Missing-data rule: No authority record never becomes a pass. Mixed or unclear statuses require review.
- Decision boundary: Return AUTHORIZED FOR STATED USE, NOT AUTHORIZED, or REVIEW REQUIRED.
- Required follow-through: Stop the transaction when required authority is absent; otherwise continue to insurance and policy qualification.

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

