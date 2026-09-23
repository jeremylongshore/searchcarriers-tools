---
name: searchcarriers-risk-engine
description: "Analyzes verified SearchCarriers evidence for risk engine mcp operator. Use when a user asks, \"Run the Risk Engine with our supplied carrier\u2026\". Trigger with \"Run the Risk Engine with our\u2026\"."
allowed-tools: Read, mcp__searchcarriers-risk-engine__qualification_reports, mcp__searchcarriers-risk-engine__risk_score, mcp__searchcarriers-risk-engine__vetting_check, mcp__searchcarriers-risk-engine__insurance_check, mcp__searchcarriers-risk-engine__compliance_audit
argument-hint: '[DOT, docket, VIN, carrier list, or workflow input]'
version: 0.3.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Claude Code and MCP-capable clients; requires Python 3.10+, network access to searchcarriers.com, and an eligible SearchCarriers plan.
metadata:
  tier: pro
tags:
- searchcarriers
- motor-carrier
- evidence
- pro
---

# Risk Engine MCP Operator

Risk Engine MCP Operator helps an operator use risk tools as transparent evidence and policy checks without presenting modeled scores as official ratings. It solves this operational failure: Composite scores and default thresholds can hide assumptions or be mistaken for FMCSA determinations.

## Overview

The workflow is **identify → fetch → reconcile → decide → act**. API data is
licensed research evidence, not an endorsement, official safety rating, or guarantee.
Keep the human or named company policy as the decision owner.

The bounded result is: Return EVIDENCE, REVIEW, or the named policy verdict; never call a modeled risk score an official safety rating.

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

**Routes/tools:** MCP tools: qualification_reports, risk_score, vetting_check, insurance_check, compliance_audit

Prefer named upstream qualification results. When using modeled tools, disclose every threshold, input, missing field, and that the result is advisory.

Call the narrowest MCP tool listed in **Routes/tools** and pass only the documented input fields. Example MCP input:

```json
{"dot_number": "1234567"}
```

The MCP server selects v3, v2, or v1 from the shared contract and returns the API version in its evidence. Never bypass a structured tool error by inventing a route.

### Step 4: Reconcile evidence

Capture: Tool/version, policy or model name, factors/rules, observed values, missing evidence, source/as-of, verdict, and next action.

Keep facts, policy tests, modeled indicators, and analyst judgment in separate
fields. Preserve zeros; represent absent fields as `unknown` with a reason.

### Step 5: Decide and prescribe the next action

Return EVIDENCE, REVIEW, or the named policy verdict; never call a modeled risk score an official safety rating.

**Next action:** Resolve failed evidence, obtain the named policy, or escalate reviews before onboarding.


Registered tool identifiers: `mcp__searchcarriers-risk-engine__qualification_reports`, `mcp__searchcarriers-risk-engine__risk_score`, `mcp__searchcarriers-risk-engine__vetting_check`, `mcp__searchcarriers-risk-engine__insurance_check`, `mcp__searchcarriers-risk-engine__compliance_audit`.

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

**Should trigger:** “Run the Risk Engine with our supplied carrier policy and show every rule.”

Produce the bounded record, show the decisive evidence and unknowns, and give one
operational next action.

**Should not trigger:** “Find carriers near Dallas.”

Route that request to the narrower SearchCarriers skill whose job matches it.

## Error Handling

| Condition | Required response |
|---|---|
| Identity conflict or multiple matches | Stop and return `REVIEW`; request a USDOT or docket. |
| Missing field or empty data | Partial endpoint failure forces REVIEW for affected dimensions. |
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
