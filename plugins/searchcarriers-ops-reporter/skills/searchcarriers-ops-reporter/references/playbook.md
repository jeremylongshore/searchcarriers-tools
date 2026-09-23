# Carrier Decision Report Builder decision playbook

## Operational problem

Pretty reports can conceal missing evidence, stale data, and the difference between API facts and analyst judgment.

## Evidence contract

- Job: turn carrier evidence into an auditable report or export without changing the underlying verdict.
- API surface: MCP tools: generate_report, generate_fleet, generate_compare, export_data.
- Required evidence: Subject identity, purpose, evidence sections, policy/model disclosure, missing evidence, human decision, source/as-of, and export manifest.
- Missing-data rule: If an upstream section failed, mark the report incomplete and include the exact recovery action.
- Decision boundary: Return READY or INCOMPLETE; formatting may not upgrade REVIEW to PASS.
- Required follow-through: Have the decision owner sign off, then retain the report according to internal policy.

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

