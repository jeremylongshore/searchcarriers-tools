# Carrier Identity Risk Triage decision playbook

## Operational problem

Identity theft, spoofed contacts, unauthorized USDOT use, and carrier-involved theft defeat single-source checks.

## Evidence contract

- Job: triage carrier identity anomalies and prescribe independent verification without accusing a carrier of fraud.
- API surface: GET /api/v3/company/{dot}?fields=contact,authorities,insurance,equipment,risk_factors; GET /api/v3/company/{dot}/equipment; GET /api/v1/search/by-vin/{vin}.
- Required evidence: Claimed identity, authoritative API identity, exact mismatches, timing anomalies, shared identifiers, verification performed, missing evidence, and source/as-of.
- Missing-data rule: Missing contact or equipment evidence increases uncertainty; it does not prove fraud.
- Decision boundary: Return NO MATERIAL ANOMALY OBSERVED, HOLD FOR VERIFICATION, or STOP AND ESCALATE. Never label an entity fraudulent from API data alone.
- Required follow-through: Verify through independent contact channels, preserve evidence, and follow FMCSA reporting guidance when misuse is suspected.

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

