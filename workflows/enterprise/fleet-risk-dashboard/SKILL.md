---
name: searchcarriers-fleet-risk-dashboard
description: Weekly fleet-wide risk analysis across all watched carriers with trend tracking and executive summary. Use when assessing fleet risk.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: enterprise
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- workflow
---

# Fleet Risk Dashboard -- Workflow Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This workflow orchestrates a fleet-wide risk analysis across all carriers on the Watchdog watch list, producing an executive dashboard with risk distribution, trend tracking, and actionable summaries. It coordinates all four stackable plugins plus Watchdog: Carrier Intel (carrier profiles), Risk Engine (scoring), Ops Reporter (reports and comparisons), and Watchdog (watch list and compliance drift).

The pipeline follows this execution path:

```
manage_watchlist (Watchdog) -- list all monitored carriers
    |
    v
[For each watched carrier]
    |-- carrier_profile (Carrier Intel)
    |-- risk_score (Risk Engine)
    |
    v
generate_fleet (Ops Reporter) -- fleet-level equipment analysis
    |
    v
generate_compare (Ops Reporter) -- top 5 riskiest carriers
    |
    v
[Aggregate into executive dashboard]
    |-- Fleet health metrics
    |-- Risk distribution
    |-- Trend indicators (vs. prior run)
    |-- Action items
    |
    v
route_alert (Watchdog) -- distribute dashboard via email/Slack
```

This workflow transforms raw monitoring data into a strategic overview that safety directors, compliance officers, and executive leadership can use to assess fleet-wide risk posture at a glance. It is designed to run weekly but can be triggered on demand.

## Prerequisites

- **Minimum tier**: Enterprise (unlimited watch list, all plugins required)
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid Bearer token
- MCP servers running: `searchcarriers-carrier-intel`, `searchcarriers-risk-engine`, `searchcarriers-ops-reporter`, `searchcarriers-watchdog`
- API base URL: `https://searchcarriers.com/api/v1`
- Authentication format: `Authorization: Bearer {id}|{token}` (Laravel Sanctum)
- At least 5 carriers on the watch list (dashboard is most useful with 10+)
- Prior dashboard run data (optional, enables trend tracking)

## Instructions

### Stage 1: Watch List Retrieval

Call `manage_watchlist` from the Watchdog plugin with `action: "list"` to retrieve all actively monitored carriers.

**Watch list data collected per carrier:**

| Field | Source | Purpose |
|-------|--------|---------|
| DOT number | Watchlist entry | Primary identifier for all downstream calls |
| Legal name | Watchlist entry | Display in dashboard |
| Watch ID | Watchlist entry | Trace the configured watch |

Process every carrier returned by `manage_watchlist`. Do not infer monitoring
states, watch dates, alert counts, or baseline status. Report the total carrier
count before proceeding.

### Stage 2: Carrier Profiling and Risk Scoring

For each active carrier on the watch list, run two calls in sequence.

**Step 2a: Carrier Profile**

Call `carrier_profile` from the Carrier Intel plugin for each carrier. This retrieves the base carrier record, authority details, and insurance records in a single call.

**Data collected per carrier:**

| Field | Source | Dashboard Use |
|-------|--------|--------------|
| Status | carrier_profile | Fleet status distribution |
| Power units | carrier_profile | Total fleet capacity |
| Total drivers | carrier_profile | Workforce metric |
| Safety rating | carrier_profile | Safety distribution chart |
| Operation type | carrier_profile | Fleet composition |
| Insurance status | carrier_profile | Coverage health metric |
| Authority status | carrier_profile | Legal compliance metric |
| MCS-150 date | carrier_profile | Filing currency metric |

**Step 2b: Risk Score**

Call `risk_score` from the Risk Engine plugin for each carrier.

**Data collected per carrier:**

| Field | Source | Dashboard Use |
|-------|--------|--------------|
| Composite score | risk_score `_pipeline.data` | Risk distribution, ranking, trends |
| Risk level | risk_score `_pipeline.data` | Level distribution pie chart |
| Factor breakdown | risk_score `_pipeline.data` | Factor heatmap across fleet |
| Top risk factor | risk_score `_pipeline.data` | Most common fleet-wide risk theme |

**Rate management:** With a large watch list, this stage is the most API-intensive. For a 50-carrier watch list, expect approximately 250-300 API calls (5-6 per carrier). At 3 requests/second, this takes approximately 90-100 seconds.

**Error handling during scoring:** If `carrier_profile` or `risk_score` fails for a specific carrier, log the failure and continue with remaining carriers. Include failed carriers in the dashboard with a "scoring unavailable" indicator.

### Stage 3: Fleet Analysis

Call `generate_fleet` from the Ops Reporter plugin with the aggregated carrier profile data from Stage 2.

**Fleet analysis produces:**

| Metric | Calculation | Dashboard Section |
|--------|-------------|-------------------|
| Total power units | Sum of all carriers' power units | Fleet capacity |
| Total drivers | Sum of all carriers' drivers | Workforce |
| Average fleet size | Mean power units per carrier | Fleet profile |
| Fleet size distribution | Count of carriers per fleet size code (A-H) | Fleet composition |
| Equipment diversity | Count of unique makes/models across fleet | Equipment profile |
| Average vehicle age | Mean age of vehicles if equipment data available | Maintenance risk |

### Stage 4: Riskiest Carrier Comparison

Sort all scored carriers by `composite_score` descending and select the top 5 riskiest. Call `generate_compare` from the Ops Reporter plugin with these 5 carriers.

**Comparison produces:**

| Output | Content | Dashboard Section |
|--------|---------|-------------------|
| Comparison matrix | Side-by-side metrics for top 5 riskiest | Risk spotlight |
| Per-carrier red flags | Critical and high flags for each | Action items |
| Factor comparison | Which risk factors are elevated for each | Risk theme analysis |
| Ranking | Ordered by composite score with tiebreaker on red flag count | Priority ranking |

If the watch list has fewer than 5 carriers, compare all of them.

### Stage 5: Executive Dashboard Assembly

Aggregate all data from Stages 1-4 into the executive dashboard. The dashboard consists of six sections.

**Section 1: Fleet Health Summary**

| Metric | Value | Source |
|--------|-------|--------|
| Carriers monitored | Count of active watch list entries | Stage 1 |
| Average risk score | Mean of all composite scores | Stage 2 |
| Fleet risk level | Derived from average risk score using standard ranges | Stage 2 |
| Pass rate | Percentage of carriers at LOW or MEDIUM risk | Stage 2 |
| Carriers requiring action | Count at ELEVATED or HIGH risk | Stage 2 |
| Total fleet capacity | Sum of power units across all carriers | Stage 3 |

**Section 2: Risk Distribution**

Break down the fleet by risk level:

| Level | Count | Percentage | Visual |
|-------|-------|------------|--------|
| LOW (0-25) | N | N% | Green indicator |
| MEDIUM (26-50) | N | N% | Yellow indicator |
| ELEVATED (51-75) | N | N% | Orange indicator |
| HIGH (76-100) | N | N% | Red indicator |

**Section 3: Risk Factor Heatmap**

For each of the 7 risk factors (Safety Rating, Insurance Coverage, Authority Status, OOS Rates, Operating History, Crash History, Compliance Currency), show the fleet-wide average score:

| Factor | Fleet Average | Carriers Above 50 | Carriers Above 75 | Assessment |
|--------|--------------|--------------------|--------------------|------------|
| Safety Rating | N/100 | N | N | OK / CONCERN / CRITICAL |
| Insurance Coverage | N/100 | N | N | OK / CONCERN / CRITICAL |
| Authority Status | N/100 | N | N | OK / CONCERN / CRITICAL |
| OOS Rates | N/100 | N | N | OK / CONCERN / CRITICAL |
| Operating History | N/100 | N | N | OK / CONCERN / CRITICAL |
| Crash History | N/100 | N | N | OK / CONCERN / CRITICAL |
| Compliance Currency | N/100 | N | N | OK / CONCERN / CRITICAL |

Assessment thresholds: OK = fleet average below 25, CONCERN = fleet average 25-50, CRITICAL = fleet average above 50.

**Section 4: Trend Indicators**

If a prior dashboard run exists, calculate trends by comparing current metrics to the previous run:

| Metric | Current | Previous | Delta | Trend |
|--------|---------|----------|-------|-------|
| Average risk score | N | N | +/- N | Improving / Stable / Degrading |
| HIGH risk carriers | N | N | +/- N | Improving / Stable / Degrading |
| Pass rate | N% | N% | +/- N% | Improving / Stable / Degrading |

Trend classification:
- **Improving**: Metric moved in the favorable direction by more than 5%.
- **Stable**: Metric changed by less than 5% in either direction.
- **Degrading**: Metric moved in the unfavorable direction by more than 5%.

If no prior run data exists, display: "Trend data unavailable -- first dashboard run. Trends will appear on the next execution."

**Section 5: Top 5 Riskiest Carriers**

Display the `generate_compare` output from Stage 4 as a focused spotlight section. Include:

| Rank | DOT | Carrier Name | Risk Score | Risk Level | Top Flag | Recommended Action |
|------|-----|-------------|------------|------------|----------|-------------------|
| 1 | N | Name | N/100 | LEVEL | Flag text | Action text |
| ... | ... | ... | ... | ... | ... | ... |

For each carrier in the top 5, include a one-line recommended action:
- HIGH risk: "Suspend freight tenders pending full review."
- ELEVATED risk: "Schedule detailed risk review within 7 days."
- MEDIUM risk: "Monitor; review at next dashboard cycle."

**Section 6: Action Items**

Generate a prioritized action list derived from the dashboard analysis:

| Priority | Action | Affected Carriers | Deadline |
|----------|--------|-------------------|----------|
| CRITICAL | Review HIGH-risk carriers immediately | DOTs listed | 24 hours |
| HIGH | Investigate insurance concerns | DOTs with insurance factor > 50 | 7 days |
| HIGH | Address OOS rate trends | DOTs with OOS factor > national avg | 7 days |
| MEDIUM | Follow up on REVIEW-status carriers | DOTs at MEDIUM risk | Next cycle |
| LOW | Refresh current evidence | DOTs with incomplete noncritical data | Next cycle |

### Stage 6: Dashboard Distribution

Call `route_alert` from the Watchdog plugin to distribute the completed dashboard to configured channels.

**Distribution options:**

| Channel | Format | Recipients |
|---------|--------|------------|
| Email | HTML-formatted dashboard digest | Safety director, compliance team, executives |
| Slack | Summary message with key metrics and link to full dashboard | #carrier-risk channel |
| Webhook | JSON payload with all dashboard data | BI tools, data warehouse, custom integrations |

**Email subject format:** `[SearchCarriers Fleet Dashboard] Week of {date} -- {fleet_risk_level} Risk ({carriers_monitored} carriers)`

**Slack message format:** Summary block with fleet health metrics, risk distribution bar, top 3 action items, and link to the full dashboard.

## Examples

### Example 1: Weekly Executive Dashboard

Safety director requests the weekly fleet dashboard.

1. `manage_watchlist` returns 35 active carriers, 2 paused, 1 stale.
2. `carrier_profile` and `risk_score` for 36 carriers (35 active + 1 stale). 34 succeed, 2 score failures (API timeout).
3. `generate_fleet`: 1,247 total power units, 1,890 drivers, average fleet size 36.
4. `generate_compare` for top 5 riskiest: scores range 62-84. Top carrier has HIGH risk due to insurance lapse.
5. Dashboard assembled: average risk 31/100 (MEDIUM), 28 LOW, 4 MEDIUM, 2 ELEVATED, 1 HIGH, 1 scoring unavailable.
6. Trends vs. last week: average risk improved by 3 points (was 34), 1 fewer HIGH-risk carrier.
7. `route_alert` distributes to email (safety director) and Slack (#carrier-risk).

### Example 2: First Run (No Trend Data)

New Enterprise customer runs their first fleet dashboard with 12 watched carriers.

1. `manage_watchlist` returns 12 watched carriers.
2. `carrier_profile` and `risk_score` for all 12. All succeed.
3. `generate_fleet`: 428 total power units.
4. `generate_compare` for top 5 riskiest.
5. Dashboard assembled with all sections except trends: "Trend data unavailable -- first dashboard run."
6. Action items generated from current state analysis.
7. Dashboard distributed as a point-in-time report. Any trend baseline must be stored and compared by the calling application.

### Example 3: Dashboard with Compliance Concerns

Dashboard reveals fleet-wide compliance currency deterioration.

1. 50 carriers profiled and scored.
2. Risk factor heatmap shows Compliance Currency factor average is 55/100 (CRITICAL).
3. 18 carriers have MCS-150 filings older than 24 months.
4. Trend vs. last week: Compliance Currency factor worsened by 8 points.
5. Action items include: "CRITICAL: 18 carriers have overdue MCS-150 filings. Contact carriers to file biennial updates or risk FMCSA penalties."
6. Top 5 comparison highlights that 3 of the riskiest carriers share compliance as their top risk factor.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Empty watch list | No carriers being monitored | Report: "No carriers on watch list. Add carriers via `/sc-watch add {DOT}` before running the dashboard." |
| Watch list too small | Fewer than 5 carriers | Generate dashboard with available carriers; note: "Dashboard is most effective with 10+ carriers." |
| Bulk scoring timeout | Large watch list causes API rate limit pressure | Process in chunks of 25 carriers with pauses between chunks |
| carrier_profile failure | Individual carrier API error | Log failure; exclude carrier from scoring but include in dashboard with "data unavailable" marker |
| risk_score failure | Scoring engine error for specific carrier | Log failure; include carrier in dashboard with "scoring unavailable" marker |
| generate_fleet failure | Ops Reporter MCP error | Skip fleet analysis section; note omission in dashboard |
| generate_compare failure | Comparison engine error | Skip top 5 section; list riskiest carriers as a simple table instead |
| No prior run data | First dashboard execution or prior data expired | Skip trend section; note: "First run -- trends available next cycle." |
| route_alert failure | Notification channel misconfigured | Display dashboard in session output; report which channel failed and suggest checking configuration |
| Watchdog MCP unavailable | `searchcarriers-watchdog` server not running | Report: "Watchdog MCP required for watch list retrieval. Cannot generate fleet dashboard." |
| All MCP servers unavailable | System-level failure | Report which servers are down and recommend checking MCP configuration |

## Resources

- Watchdog plugin tools: `manage_watchlist`, `monitor_compliance`, `route_alert` -- `{baseDir}/plugins/searchcarriers-watchdog/SCHEMA.md`
- Carrier Intel plugin tools: `carrier_profile` -- `{baseDir}/plugins/searchcarriers-carrier-intel/SCHEMA.md`
- Risk Engine plugin tools: `risk_score` -- `{baseDir}/plugins/searchcarriers-risk-engine/SCHEMA.md`
- Ops Reporter plugin tools: `generate_fleet`, `generate_compare` -- `{baseDir}/plugins/searchcarriers-ops-reporter/SCHEMA.md`
- Risk score ranges: LOW (0-25), MEDIUM (26-50), ELEVATED (51-75), HIGH (76-100)
- Risk factor weights: Safety 25%, Insurance 20%, Authority 15%, OOS 15%, History 10%, Crashes 10%, Compliance 5%
- Pipeline architecture: Watchdog (MONITORING) + Carrier Intel (INPUT) + Risk Engine (ANALYSIS) + Ops Reporter (OUTPUT)
- National OOS benchmarks: vehicle ~20%, driver ~5%
- FMCSA insurance minimums: 49 CFR Part 387
- SearchCarriers API base: `https://searchcarriers.com/api/v1`
- Auth format: `Authorization: Bearer {id}|{token}` (Laravel Sanctum)
