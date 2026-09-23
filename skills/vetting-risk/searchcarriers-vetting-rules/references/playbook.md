# Policy Qualification Runner decision playbook

## Operational problem

Informal checklists drift between analysts, while hidden defaults create decisions no one can audit.

## Evidence contract

- Job: apply named company or customer criteria and return reproducible Pass, Review, or Fail evidence.
- API surface: GET /api/v2/company/{dot}/qualification-reports; GET /api/v3/company/{dot}?fields=vetting_report,risk_factors,authorities,insurance,safety,operation.
- Required evidence: Qualification name, criteria/as-of, per-rule observed value and source, Pass/Review/Fail result, missing evidence, and override record.
- Missing-data rule: If no named policy is supplied, ask for one or return evidence-only REVIEW; do not invent industry-standard thresholds.
- Decision boundary: Return the upstream or deterministic policy verdict. Missing evidence must follow the rule policy and may never silently pass.
- Required follow-through: Send failures to remediation, reviews to a human queue, and store the evidence snapshot with the decision.

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

