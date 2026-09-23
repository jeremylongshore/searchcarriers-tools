# Carrier Event Slack Formatter decision playbook

## Operational problem

Untrusted event payloads and invented alert feeds create false urgency or expose webhook secrets.

## Evidence contract

- Job: validate and format a supplied carrier-change event for Slack delivery.
- API surface: Watchdog MCP route_alert with externally supplied event; no public SearchCarriers alert-feed route.
- Required evidence: Event provenance, carrier, change, current confirmation, severity rationale, owner, and action link.
- Missing-data rule: Missing provenance or DOT is quarantined. endpoint_unavailable is not no alerts.
- Decision boundary: Return MESSAGE READY, QUARANTINED, or DELIVERY FAILED.
- Required follow-through: Send only through a configured Slack integration and preserve the delivery receipt.

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

