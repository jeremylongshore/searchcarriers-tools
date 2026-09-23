# Insurance Filing Reconciler decision playbook

## Operational problem

Insurance minimums vary by operation, and certificates can be altered or inconsistent with filed coverage.

## Evidence contract

- Job: reconcile filed insurance evidence with the requirements for the exact entity, authority, cargo, and vehicle.
- API surface: GET /api/v3/company/{dot}?fields=insurance,authorities,operation; GET /api/v1/company/{dot}/insurances.
- Required evidence: Requirement source, operation facts, active filing evidence, coverage amount/type, effective/cancellation dates, gaps, conflicts, and as-of.
- Missing-data rule: An active policy with missing amount or type is REVIEW. No returned record is not proof of no insurance until route/access errors are excluded.
- Decision boundary: Return MEETS STATED REQUIREMENT, DOES NOT MEET, or REVIEW REQUIRED. Do not apply one blanket minimum to every carrier.
- Required follow-through: Call the insurer using independently sourced contact information when documents or filings conflict; stop tendering if required coverage cannot be confirmed.

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

