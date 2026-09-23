# Carrier Relationship Mapper decision playbook

## Operational problem

Fraud investigations often overstate weak shared attributes, and common addresses or service providers create noisy links.

## Evidence contract

- Job: map evidence of shared equipment and related company records without declaring common control.
- API surface: GET /api/v3/company/{dot}; GET /api/v3/company/{dot}/equipment; GET /api/v1/search/by-vin/{vin}.
- Required evidence: Seed identity, related DOT, shared VIN or API-provided association, dates where present, source route, and confidence rationale.
- Missing-data rule: No related results is not proof of independence; state the coverage limits and unsearched identifiers.
- Decision boundary: Return CONFIRMED LINK only for an exact shared identifier, POSSIBLE LINK for weaker API evidence, and UNRESOLVED when evidence is incomplete.
- Required follow-through: Manually verify high-impact links through official records and trusted contacts before changing carrier status.

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

