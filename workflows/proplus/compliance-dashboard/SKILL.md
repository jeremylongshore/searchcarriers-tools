---
name: searchcarriers-compliance-dashboard
description: Build a current-state compliance dashboard for every carrier on the SearchCarriers watch list. Use when running weekly compliance review or exception triage.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: proplus
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- workflow
---

# Compliance Dashboard — Workflow Skill

## Overview

Build a point-in-time compliance dashboard from the documented watch list and
current API evidence. This workflow never invents monitoring states, baselines,
historical drift, alert counts, or email delivery.

> **API contract:** Use the repository `API-DISCOVERY.md` for the current
> v3/v2/v1 route map. `monitor_compliance` evaluates current evidence; it does
> not provide a historical trend feed.

## Prerequisites

- SearchCarriers Pro Plus or Enterprise access as required by the tools
- `searchcarriers-watchdog`, `searchcarriers-risk-engine`, and
  `searchcarriers-ops-reporter` MCP servers running
- `SEARCHCARRIERS_API_KEY` set in the process environment
- At least one company watch configured with `manage_watchlist`

## Instructions

### 1. Read the current watch list

Call `manage_watchlist` with `action: "list"`. Use only fields actually returned
by the tool: `id`, `dot_number`, and `carrier_name`. If the list is empty, stop
with a clear instruction to add a carrier.

```python
watch_response = manage_watchlist(action="list")
carriers = watch_response.get("carriers", [])
if not carriers:
    raise RuntimeError("No carriers are currently on the watch list.")
```

### 2. Run both compliance views

For every DOT number, call:

1. `compliance_audit` from Risk Engine for the regulatory audit.
2. `monitor_compliance` from Watchdog for the current authority, insurance,
   operating-status, and filing-freshness checks.

Process carriers sequentially or with bounded concurrency. Preserve every
missing-evidence result and tool error; never convert missing data into a pass.

```python
rows = []
for carrier in carriers:
    dot = carrier["dot_number"]
    audit = compliance_audit(dot_number=dot)
    current = monitor_compliance(dot_number=dot)
    rows.append(
        {
            "dot_number": dot,
            "carrier_name": carrier.get("carrier_name", "Unknown Carrier"),
            "audit": audit,
            "current": current,
        }
    )
```

### 3. Classify review priority

Use evidence from both tools:

| Priority | Trigger | Action |
|---|---|---|
| Critical | Either tool reports a critical failure or no active authority/insurance | Stop tendering and verify source records immediately |
| High | Failed compliance checks without a critical condition | Review before the next load |
| Review | Missing evidence, warnings, or conflicting results | Verify the missing source data |
| Clear | All available checks pass with no missing evidence | Continue normal monitoring |

If the two tools disagree, show both results and classify the carrier as
`Review`. Do not average conflicting statuses into a synthetic score.

### 4. Build the dashboard

Present these sections:

1. Run timestamp and carrier count
2. Priority totals
3. Carrier table with DOT, name, audit result, current compliance status, failed
   checks, and missing evidence
4. Critical and high-priority action queue
5. Tool errors and skipped records
6. Source and limitations note

Example table:

```markdown
| DOT | Carrier | Audit | Current status | Failed checks | Priority |
|---|---|---|---|---|---|
| 1234567 | Example Freight LLC | Review | drift | insurance coverage | High |
```

### 5. Generate optional carrier reports

For a critical or high-priority carrier, call `generate_report` for the DOT and
link or embed the resulting point-in-time report. Do not generate reports for
all carriers unless the user asks; large report sets increase API and rendering
cost.

### 6. Format an external notification when requested

`route_alert` formats a caller-supplied event for Slack, Telegram, email, or a
webhook. It does not transmit the message. Return the formatted payload and say
which external system must deliver it.

## Output

Return the dashboard, action queue, evidence gaps, run timestamp, and the list
of DOT numbers successfully checked. Include a plain statement that the output
is a point-in-time screening aid and does not constitute an official safety
rating or legal advice. Never include an API token or raw bulk API response.

## Examples

- "Build this week's compliance dashboard for every watched carrier."
- "Show only critical and high-priority compliance exceptions for the watch list."
- "Format the critical findings from this dashboard for Slack."

## Error Handling

| Condition | Action |
|---|---|
| Watch list unavailable | Stop; report the structured tool error |
| Empty watch list | Stop; suggest `manage_watchlist(action="add", dot_number=...)` |
| One carrier fails | Preserve the failure in the dashboard and continue |
| All carrier checks fail | Stop; report likely authentication, plan, or service failure |
| `get_alerts` returns `endpoint_unavailable` | Treat as expected; do not retry an undocumented route |
| Notification formatting fails | Return the dashboard and mark the message as unformatted |

## Resources

- Repository `API-DISCOVERY.md`
- `plugins/searchcarriers-watchdog/SCHEMA.md`
- `plugins/searchcarriers-risk-engine/SCHEMA.md`
- `plugins/searchcarriers-ops-reporter/SCHEMA.md`
