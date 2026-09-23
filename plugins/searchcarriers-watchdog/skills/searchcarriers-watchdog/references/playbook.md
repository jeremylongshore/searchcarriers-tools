# Carrier Watch Operations decision playbook

## Operational problem

Teams assume a configured watch guarantees alerts even though the public API exposes watch state but no alert-feed endpoint.

## Evidence contract

- Job: manage company watch types and turn supplied change events into review work.
- API surface: MCP tools: manage_watchlist, get_alerts, route_alert, monitor_compliance; GET/POST /api/v1/company/{dot}/watch.
- Required evidence: DOT, requested/current watch types, API result, event provenance, current compliance snapshot, delivery attempt, and as-of.
- Missing-data rule: get_alerts endpoint_unavailable means unavailable, not zero events. Delivery failure does not undo watch state.
- Decision boundary: Return WATCH CONFIGURED, WATCH REMOVED, REVIEW EVENT, or DELIVERY FAILED. Never report no alerts from an unavailable feed.
- Required follow-through: Fix the external event source or delivery channel and retain a retry receipt.

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

