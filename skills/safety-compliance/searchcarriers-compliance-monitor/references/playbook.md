# Compliance Snapshot Builder decision playbook

## Operational problem

One-time onboarding checks age immediately, and teams often mistake a current snapshot for continuous monitoring.

## Evidence contract

- Job: produce a point-in-time carrier compliance snapshot and identify what must be rechecked.
- API surface: GET /api/v3/company/{dot}?fields=authorities,insurance,safety,oos_orders,operation,risk_factors; GET /api/v1/company/{dot}/watch.
- Required evidence: DOT status, authorities, insurance filings, safety/OOS evidence, watch state, missing data, policy source, and as-of timestamp.
- Missing-data rule: API or field absence creates REVIEW. Watch configuration without an alert feed is not proof that delivery is working.
- Decision boundary: Return CURRENTLY CLEAR, ACTION REQUIRED, or REVIEW REQUIRED; separately state whether monitoring is configured.
- Required follow-through: Set the appropriate watch types and define an external review cadence or notification input.

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

