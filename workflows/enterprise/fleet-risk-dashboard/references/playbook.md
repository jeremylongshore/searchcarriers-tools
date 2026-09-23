# Fleet Risk Exception Dashboard decision playbook

## Operational problem

Large panels need triage, but opaque scores and missing-data rows can send analysts to the wrong carriers.

## Evidence contract

- Job: rank a carrier panel by actionable evidence exceptions without hiding uncertainty behind a composite score.
- API surface: Carrier Intel, Risk Engine, qualification reports, and Ops Reporter MCP tools.
- Required evidence: Panel hash/run, policy, per-carrier verdict, evidence exceptions, modeled-factor disclosure, missing data, freshness, owner, and action.
- Missing-data rule: Missing and stale records have their own priority queue and do not receive reassuring scores.
- Decision boundary: Return READY, PARTIAL, or STALE; the top queue is based on explicit exceptions and policy results.
- Required follow-through: Assign exception owners, refresh stale records, and retain the run snapshot for comparison.

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

