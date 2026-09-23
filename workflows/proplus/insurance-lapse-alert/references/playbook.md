# Insurance Change Review decision playbook

## Operational problem

A cancellation notice may be future-dated, replaced, stale, or unrelated to the required coverage, while false alarms disrupt loads.

## Evidence contract

- Job: evaluate a supplied insurance change or current filing and create a bounded response.
- API surface: GET /api/v3/company/{dot}?fields=insurance,authorities,operation; GET /api/v1/company/{dot}/insurances.
- Required evidence: Event source/time, current filing, replacement evidence, requirement source, affected loads, classification, owner, and deadline.
- Missing-data rule: An unavailable refetch or unknown requirement is UNRESOLVED, not clear.
- Decision boundary: Return NO CURRENT GAP, UPCOMING REVIEW, CURRENT GAP, or UNRESOLVED.
- Required follow-through: Hold affected tendering when required coverage cannot be confirmed and verify with the insurer through an independent contact.

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

