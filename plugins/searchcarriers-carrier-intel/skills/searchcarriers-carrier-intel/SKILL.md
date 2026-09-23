---
name: searchcarriers-carrier-intel
description: "Analyzes verified SearchCarriers evidence for carrier intel mcp operator. Use when a user asks, \"Use Carrier Intel to source van carriers on an\u2026\". Trigger with \"Use Carrier Intel to source van\u2026\"."
allowed-tools: Read, mcp__searchcarriers-carrier-intel__carrier_lookup, mcp__searchcarriers-carrier-intel__carrier_profile, mcp__searchcarriers-carrier-intel__entity_map, mcp__searchcarriers-carrier-intel__fleet_summary
argument-hint: '[DOT, docket, VIN, carrier list, or workflow input]'
version: 0.3.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Grok Build, Claude Code, and other MCP-capable clients; requires Python 3.10+, network access to searchcarriers.com, and an eligible SearchCarriers plan.
metadata:
  tier: free
tags:
- searchcarriers
- motor-carrier
- evidence
- free
---

# Carrier Intel MCP Operator

Carrier Intel MCP Operator helps an operator use the Carrier Intel MCP tools for identifier resolution, filtered sourcing, profiles, relationship evidence, and fleet summaries. It solves this operational failure: Operators need the right tool and route without manually translating API versions or treating search candidates as approved carriers.

## Overview

The workflow is **identify → fetch → reconcile → decide → act**. API data is
licensed research evidence, not an endorsement, official safety rating, or guarantee.
Keep the human or named company policy as the decision owner.

The bounded result is: Return identity/candidate/fleet evidence only; qualification belongs to the named policy workflow.

## Prerequisites

- Set `SEARCHCARRIERS_API_KEY` to a SearchCarriers bearer token with the required tier.
- Confirm the subject identifier, intended movement or decision, and named policy when applicable.
- Read [`API-DISCOVERY.md`](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md) with the `Read` tool before changing routes or parameters.
- Use the registered MCP tools listed in `allowed-tools`; their server process owns bearer authentication and route selection.

Authentication is `Authorization: Bearer $SEARCHCARRIERS_API_KEY`; never print,
commit, or place the token in a URL. Do not commit live API responses.

## Instructions

### Step 1: Define the decision

Write one sentence naming the subject, the operational use, the evidence window,
and who owns the final decision. If a policy threshold is required, obtain the
named policy instead of inventing an “industry standard.”

### Step 2: Resolve identity

Prefer USDOT or docket identifiers. Treat name-only matches as ambiguous until
legal name, location, and identifiers agree. Stop on conflicting identity.

### Step 3: Fetch the smallest evidence set

**Routes/tools:** MCP tools: carrier_lookup, carrier_profile, entity_map, fleet_summary

Use carrier_lookup for exact identity or advanced sourcing filters, carrier_profile for selected due-diligence sections, entity_map for exact VIN links, and fleet_summary for equipment evidence.

Call the narrowest MCP tool listed in **Routes/tools** and pass only the documented input fields. Example MCP input:

```json
{"dot_number": "1234567"}
```

The MCP server selects v3, v2, or v1 from the shared contract and returns the API version in its evidence. Never bypass a structured tool error by inventing a route.

### Step 4: Reconcile evidence

Capture: Tool name/input, API version, identity, selected evidence, missing fields, pagination, and next required check.

Keep facts, policy tests, modeled indicators, and analyst judgment in separate
fields. Preserve zeros; represent absent fields as `unknown` with a reason.

### Step 5: Decide and prescribe the next action

Return identity/candidate/fleet evidence only; qualification belongs to the named policy workflow.

**Next action:** Route selected carriers to authority, insurance, safety, or qualification review.


Registered tool identifiers: `mcp__searchcarriers-carrier-intel__carrier_lookup`, `mcp__searchcarriers-carrier-intel__carrier_profile`, `mcp__searchcarriers-carrier-intel__entity_map`, `mcp__searchcarriers-carrier-intel__fleet_summary`.

## Output

Return this compact decision record:

```yaml
subject: "DOT or input identifier"
purpose: "the exact operational question"
status: "bounded status from this skill"
evidence:
  - fact: "observed value"
    source: "API route or MCP tool"
    as_of: "timestamp or source date"
missing_evidence: []
policy_or_method: "named policy, evidence-only, or disclosed model"
next_action: "owner and concrete action"
limitations: "coverage, freshness, and inference limits"
```

Every material claim needs a source and as-of value. Totals must reconcile to
detail rows. The output must say whether any result is partial.

## Examples

**Should trigger:** “Use Carrier Intel to source van carriers on an Alabama-to-Texas lane.”

Produce the bounded record, show the decisive evidence and unknowns, and give one
operational next action.

**Should not trigger:** “Write a TMS migration plan.”

Route that request to the narrower SearchCarriers skill whose job matches it.

## Error Handling

| Condition | Required response |
|---|---|
| Identity conflict or multiple matches | Stop and return `REVIEW`; request a USDOT or docket. |
| Missing field or empty data | A tool error is evidence of unavailable data, not a negative carrier fact. |
| `401` | Stop; report invalid/missing credentials without exposing them. |
| `403` | Stop; identify the route and required plan/access. |
| `404` | Recheck the identifier and route; do not treat it as adverse carrier evidence. |
| `422` | Remove unsupported parameters and compare with the API contract. |
| `429` | Honor `Retry-After`; use bounded retry and preserve progress. |
| `5xx` or timeout | Retry with bounded backoff, then return partial/unavailable. |

## Resources

- [Customer one-pager](docs/ONE-PAGER.md)
- [Customer one-pager PDF](docs/ONE-PAGER.pdf)
- [Decision playbook](references/playbook.md)
- [Repository API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
- [SearchCarriers public API](https://searchcarriers.com/docs/api)
- [SearchCarriers terms](https://searchcarriers.com/terms-of-service)
