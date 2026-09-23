# Carrier Intel MCP Operator decision playbook

## Operational problem

Operators need the right tool and route without manually translating API versions or treating search candidates as approved carriers.

## Evidence contract

- Job: use the Carrier Intel MCP tools for identifier resolution, filtered sourcing, profiles, relationship evidence, and fleet summaries.
- API surface: MCP tools: carrier_lookup, carrier_profile, entity_map, fleet_summary.
- Required evidence: Tool name/input, API version, identity, selected evidence, missing fields, pagination, and next required check.
- Missing-data rule: A tool error is evidence of unavailable data, not a negative carrier fact.
- Decision boundary: Return identity/candidate/fleet evidence only; qualification belongs to the named policy workflow.
- Required follow-through: Route selected carriers to authority, insurance, safety, or qualification review.

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

