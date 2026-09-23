# Trusted Contact Consistency Check decision playbook

## Operational problem

Spoofed email, caller ID, and recently changed FMCSA contacts make a matching string insufficient proof of identity.

## Evidence contract

- Job: compare supplied contact details with carrier records and define an independent callback step.
- API surface: GET /api/v3/company/{dot}?fields=contact,risk_factors; GET /api/v1/company/{dot}/contact-details.
- Required evidence: Supplied contact, returned contact, comparison result, freshness/change evidence, verification channel, missing fields, and as-of.
- Missing-data rule: Missing contacts are UNVERIFIED. Generic or VoIP metadata may raise review but is not proof of fraud.
- Decision boundary: Return CONSISTENT, MISMATCH, or UNVERIFIED. Never claim that the API alone verified the person communicating.
- Required follow-through: Call a known number, confirm dispatch and equipment details, and hold the load until a material mismatch is resolved.

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
