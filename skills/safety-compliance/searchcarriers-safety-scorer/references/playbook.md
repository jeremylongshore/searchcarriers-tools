# Safety Evidence Interpreter decision playbook

## Operational problem

Teams confuse FMCSA safety ratings, BASIC information, crashes, and missing data, leading to false passes and false rejections.

## Evidence contract

- Job: explain a carrier safety record without inventing a universal safety score.
- API surface: GET /api/v3/company/{dot}?fields=safety,basic_scores,risk_factors; GET /api/v3/company/{dot}/crashes.
- Required evidence: Rating with date, safety measures with observation windows, crash facts, inspection exposure, missing fields, and source/as-of.
- Missing-data rule: Not rated is not satisfactory or unsafe. Zero inspections is low exposure, not proof of safety.
- Decision boundary: Return CLEAR EVIDENCE, CONCERN, or REVIEW REQUIRED under the caller policy; do not create an official score.
- Required follow-through: Escalate concerns to the caller policy or SearchCarriers qualification; verify official status when the decision is consequential.

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

