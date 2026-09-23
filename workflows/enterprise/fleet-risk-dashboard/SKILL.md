---
name: searchcarriers-fleet-risk-dashboard
description: "Analyzes carrier evidence for fleet risk exception dashboard. Use when a user asks, \"Build this week\u2019s fleet exception dashboard for our\u2026\". Trigger with \"Build this week\u2019s fleet exception\u2026\"."
allowed-tools: Read, Bash(curl:*), Bash(python:*)
argument-hint: '[DOT, docket, VIN, carrier list, or workflow input]'
version: 0.3.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Claude Code and MCP-capable clients; requires Python 3.10+, network access to searchcarriers.com, and an eligible SearchCarriers plan.
metadata:
  tier: enterprise
tags:
- searchcarriers
- motor-carrier
- evidence
- enterprise
---

# Fleet Risk Exception Dashboard

Fleet Risk Exception Dashboard helps an operator rank a carrier panel by actionable evidence exceptions without hiding uncertainty behind a composite score. It solves this operational failure: Large panels need triage, but opaque scores and missing-data rows can send analysts to the wrong carriers.

## Overview

The workflow is **identify → fetch → reconcile → decide → act**. API data is
licensed research evidence, not an endorsement, official safety rating, or guarantee.
Keep the human or named company policy as the decision owner.

The bounded result is: Return READY, PARTIAL, or STALE; the top queue is based on explicit exceptions and policy results.

## Prerequisites

- Set `SEARCHCARRIERS_API_KEY` to a SearchCarriers bearer token with the required tier.
- Confirm the subject identifier, intended movement or decision, and named policy when applicable.
- Read [`API-DISCOVERY.md`](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md) with the `Read` tool before changing routes or parameters.
- Use `Bash(curl:*)` for API requests and `Bash(python:*)` only for local JSON validation or deterministic reshaping.

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

**Routes/tools:** Carrier Intel, Risk Engine, qualification reports, and Ops Reporter MCP tools

Pin the panel and policy, collect current evidence, separate official/API facts from modeled factors, rank Fail then Review then collection errors, and show exposure/freshness.

For a direct API request, use the documented route and selected fields:

```bash
curl --fail-with-body --get   "https://searchcarriers.com/api/v3/company/$DOT_NUMBER"   --header "Authorization: Bearer $SEARCHCARRIERS_API_KEY"   --header "Accept: application/json"   --data-urlencode "fields=contact,authorities,insurance,safety,operation,risk_factors"
```

Use the specialty v1 or qualification v2 route listed above when the job requires
it; never rewrite every route to the highest version.

### Step 4: Reconcile evidence

Capture: Panel hash/run, policy, per-carrier verdict, evidence exceptions, modeled-factor disclosure, missing data, freshness, owner, and action.

Keep facts, policy tests, modeled indicators, and analyst judgment in separate
fields. Preserve zeros; represent absent fields as `unknown` with a reason.

### Step 5: Decide and prescribe the next action

Return READY, PARTIAL, or STALE; the top queue is based on explicit exceptions and policy results.

**Next action:** Assign exception owners, refresh stale records, and retain the run snapshot for comparison.

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

**Should trigger:** “Build this week’s fleet exception dashboard for our carrier panel.”

Produce the bounded record, show the decisive evidence and unknowns, and give one
operational next action.

**Should not trigger:** “Check one email address.”

Route that request to the narrower SearchCarriers skill whose job matches it.

## Error Handling

| Condition | Required response |
|---|---|
| Identity conflict or multiple matches | Stop and return `REVIEW`; request a USDOT or docket. |
| Missing field or empty data | Missing and stale records have their own priority queue and do not receive reassuring scores. |
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
