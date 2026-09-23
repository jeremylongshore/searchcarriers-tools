---
name: searchcarriers-watchdog
description: "Analyzes carrier evidence for carrier watch operations. Use when a user asks, \"Watch DOT 1234567 for details and inspections, then\u2026\". Trigger with \"Watch DOT 1234567 for details and\u2026\"."
allowed-tools: Read, mcp__searchcarriers-watchdog__manage_watchlist, mcp__searchcarriers-watchdog__get_alerts, mcp__searchcarriers-watchdog__route_alert, mcp__searchcarriers-watchdog__monitor_compliance
argument-hint: '[DOT, docket, VIN, carrier list, or workflow input]'
version: 0.3.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Claude Code and MCP-capable clients; requires Python 3.10+, network access to searchcarriers.com, and an eligible SearchCarriers plan.
metadata:
  tier: proplus
tags:
- searchcarriers
- motor-carrier
- evidence
- proplus
---

# Carrier Watch Operations

Carrier Watch Operations helps an operator manage company watch types and turn supplied change events into review work. It solves this operational failure: Teams assume a configured watch guarantees alerts even though the public API exposes watch state but no alert-feed endpoint.

## Overview

The workflow is **identify → fetch → reconcile → decide → act**. API data is
licensed research evidence, not an endorsement, official safety rating, or guarantee.
Keep the human or named company policy as the decision owner.

The bounded result is: Return WATCH CONFIGURED, WATCH REMOVED, REVIEW EVENT, or DELIVERY FAILED. Never report no alerts from an unavailable feed.

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

**Routes/tools:** MCP tools: manage_watchlist, get_alerts, route_alert, monitor_compliance; GET/POST /api/v1/company/{dot}/watch

Read current watch state, synchronize requested watch_types, verify the read-back, and accept change events only from a documented external source.

Call the narrowest MCP tool listed in **Routes/tools** and pass only the documented input fields. Example MCP input:

```json
{"dot_number": "1234567"}
```

The MCP server selects v3, v2, or v1 from the shared contract and returns the API version in its evidence. Never bypass a structured tool error by inventing a route.

### Step 4: Reconcile evidence

Capture: DOT, requested/current watch types, API result, event provenance, current compliance snapshot, delivery attempt, and as-of.

Keep facts, policy tests, modeled indicators, and analyst judgment in separate
fields. Preserve zeros; represent absent fields as `unknown` with a reason.

### Step 5: Decide and prescribe the next action

Return WATCH CONFIGURED, WATCH REMOVED, REVIEW EVENT, or DELIVERY FAILED. Never report no alerts from an unavailable feed.

**Next action:** Fix the external event source or delivery channel and retain a retry receipt.


Registered tool identifiers: `mcp__searchcarriers-watchdog__manage_watchlist`, `mcp__searchcarriers-watchdog__get_alerts`, `mcp__searchcarriers-watchdog__route_alert`, `mcp__searchcarriers-watchdog__monitor_compliance`.

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

**Should trigger:** “Watch DOT 1234567 for details and inspections, then verify read-back.”

Produce the bounded record, show the decisive evidence and unknowns, and give one
operational next action.

**Should not trigger:** “Create a PDF comparison.”

Route that request to the narrower SearchCarriers skill whose job matches it.

## Error Handling

| Condition | Required response |
|---|---|
| Identity conflict or multiple matches | Stop and return `REVIEW`; request a USDOT or docket. |
| Missing field or empty data | get_alerts endpoint_unavailable means unavailable, not zero events. Delivery failure does not undo watch state. |
| `401` | Stop; report invalid/missing credentials without exposing them. |
| `403` | Stop; identify the route and required plan/access. |
| `404` | Recheck the identifier and route; do not treat it as adverse carrier evidence. |
| `422` | Remove unsupported parameters and compare with the API contract. |
| `429` | Honor `Retry-After`; use bounded retry and preserve progress. |
| `5xx` or timeout | Retry with bounded backoff, then return partial/unavailable. |

## Resources

- [Decision playbook](references/playbook.md)
- [Repository API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
- [SearchCarriers public API](https://searchcarriers.com/docs/api)
- [SearchCarriers terms](https://searchcarriers.com/terms-of-service)
