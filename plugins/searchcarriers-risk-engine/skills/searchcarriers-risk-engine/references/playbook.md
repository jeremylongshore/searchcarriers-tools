# Risk Engine MCP Operator decision playbook

## Operational problem

Composite scores and default thresholds can hide assumptions or be mistaken for FMCSA determinations.

## Evidence contract

- Job: use risk tools as transparent evidence and policy checks without presenting modeled scores as official ratings.
- API surface: MCP tools: risk_score, vetting_check, insurance_check, compliance_audit; API v2 qualification reports when available.
- Required evidence: Tool/version, policy or model name, factors/rules, observed values, missing evidence, source/as-of, verdict, and next action.
- Missing-data rule: Partial endpoint failure forces REVIEW for affected dimensions.
- Decision boundary: Return EVIDENCE, REVIEW, or the named policy verdict; never call a modeled risk score an official safety rating.
- Required follow-through: Resolve failed evidence, obtain the named policy, or escalate reviews before onboarding.

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

