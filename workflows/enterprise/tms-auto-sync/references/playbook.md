# Approved TMS Change Application decision playbook

## Operational problem

Automated status writes can strand loads or overwrite local ownership fields when events are stale, duplicated, or incomplete.

## Evidence contract

- Job: apply an approved carrier change set idempotently and prove the result.
- API surface: API Bridge tms_sync; current SearchCarriers company/qualification evidence; local TMS adapter.
- Required evidence: Approval, event/as-of, idempotency key, before/after, protected fields, write result, reread result, and rollback receipt.
- Missing-data rule: No approval, stale source data, ambiguous identity, or reread mismatch prevents completion.
- Decision boundary: Return APPLIED, NOOP, CONFLICT, or ROLLED BACK per carrier.
- Required follow-through: Resolve conflicts and rerun only failed idempotency keys.

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

