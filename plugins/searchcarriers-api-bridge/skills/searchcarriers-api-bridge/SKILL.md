---
name: searchcarriers-api-bridge
description: "Analyzes verified SearchCarriers evidence for carrier integration operator. Use when a user asks, \"Health-check the API and prepare a resumable\u2026\". Trigger with \"Health-check the API and prepare a\u2026\"."
allowed-tools: Read, mcp__searchcarriers-api-bridge__api_health, mcp__searchcarriers-api-bridge__bulk_lookup, mcp__searchcarriers-api-bridge__tms_sync, mcp__searchcarriers-api-bridge__webhook_manage
argument-hint: '[DOT, docket, VIN, carrier list, or workflow input]'
version: 0.3.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Grok Build, Claude Code, and other MCP-capable clients; requires Python 3.10+, network access to searchcarriers.com, and an eligible SearchCarriers plan.
metadata:
  tier: smb
tags:
- searchcarriers
- motor-carrier
- evidence
- smb
---

# Carrier Integration Operator

Carrier Integration Operator helps an operator run API health, resumable bulk lookup, dry-run TMS reconciliation, and local downstream webhook configuration. It solves this operational failure: Integration failures become silent data drift when health, partial success, local webhook ownership, and rollback are not explicit.

## Overview

The workflow is **identify → fetch → reconcile → decide → act**. API data is
licensed research evidence, not an endorsement, official safety rating, or guarantee.
Keep the human or named company policy as the decision owner.

The bounded result is: Return HEALTHY/DEGRADED, COMPLETE/PARTIAL, or PROPOSED/APPLIED with exact scope.

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

**Routes/tools:** MCP tools: api_health, bulk_lookup, tms_sync, webhook_manage

Probe documented routes, run batches with per-record status, require dry-run before TMS changes, and label webhook_manage as local configuration rather than a SearchCarriers webhook API.

Call the narrowest MCP tool listed in **Routes/tools** and pass only the documented input fields. Example MCP input:

```json
{"dot_number": "1234567"}
```

The MCP server selects v3, v2, or v1 from the shared contract and returns the API version in its evidence. Never bypass a structured tool error by inventing a route.

### Step 4: Reconcile evidence

Capture: Route health without records, batch run receipts, TMS diff/result, local webhook configuration path, errors, and rollback evidence.

Keep facts, policy tests, modeled indicators, and analyst judgment in separate
fields. Preserve zeros; represent absent fields as `unknown` with a reason.

### Step 5: Decide and prescribe the next action

Return HEALTHY/DEGRADED, COMPLETE/PARTIAL, or PROPOSED/APPLIED with exact scope.

**Next action:** Retry only transient failures, review TMS conflicts, and test downstream delivery separately.


Registered tool identifiers: `mcp__searchcarriers-api-bridge__api_health`, `mcp__searchcarriers-api-bridge__bulk_lookup`, `mcp__searchcarriers-api-bridge__tms_sync`, `mcp__searchcarriers-api-bridge__webhook_manage`.

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

**Should trigger:** “Health-check the API and prepare a resumable 500-carrier refresh.”

Produce the bounded record, show the decisive evidence and unknowns, and give one
operational next action.

**Should not trigger:** “Interpret one carrier safety rating.”

Route that request to the narrower SearchCarriers skill whose job matches it.

## Error Handling

| Condition | Required response |
|---|---|
| Identity conflict or multiple matches | Stop and return `REVIEW`; request a USDOT or docket. |
| Missing field or empty data | 403 means tier/access; 429 honors Retry-After; partial runs retain successful records and an error manifest. |
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
