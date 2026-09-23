# Inspection Pattern Analyzer decision playbook

## Operational problem

Raw violation totals punish larger fleets and tiny samples make percentages look decisive.

## Evidence contract

- Job: find repeat inspection and violation patterns with exposure-aware evidence.
- API surface: GET /api/v1/company/{dot}/inspections; GET /api/v1/company/{dot}/out-of-service-orders; GET /api/v3/company/{dot}?fields=inspections,oos_percents.
- Required evidence: Window, inspection count, violations, OOS counts and denominators, repeat categories, trend basis, formal orders, and coverage gaps.
- Missing-data rule: No inspections means insufficient exposure. Missing violation detail prevents category conclusions.
- Decision boundary: Return STABLE, DETERIORATING, IMPROVING, or INSUFFICIENT EXPOSURE only when the data supports that comparison.
- Required follow-through: Review repeat severe patterns, recent formal orders, or a worsening trend with a safety specialist before qualification.

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

