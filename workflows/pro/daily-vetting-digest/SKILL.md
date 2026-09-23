---
name: searchcarriers-daily-vetting-digest
description: Auto-vet all watched carriers and generate a daily email digest with pass/review/fail summaries. Use when scheduling vetting reports.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: pro
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- workflow
---

# Daily Vetting Digest -- Workflow Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This workflow orchestrates the Ops Reporter and Watchdog plugins into an automated daily vetting cycle. It retrieves every carrier on the active watch list, runs risk scoring and vetting checks against each one, and assembles the results into a single email-ready digest with clear pass/review/fail breakdowns.

The digest answers the question every freight ops team asks each morning: "Are all my carriers still qualified to haul?" Instead of manually running individual vetting reports, this workflow batch-processes the entire watched fleet and surfaces only the carriers that need human attention.

Pipeline flow: Watchdog (`manage_watchlist`) provides the carrier roster. Risk Engine (`risk_score`, `vetting_check`) evaluates each carrier. Ops Reporter (`generate_report`) produces detailed reports for failures. Watchdog (`route_alert`) formats the final digest for email delivery.

## Prerequisites

- **Minimum tier**: Pro (requires Ops Reporter, Watchdog, and Risk Engine plugins)
- MCP servers running: `searchcarriers-ops-reporter`, `searchcarriers-watchdog`, `searchcarriers-risk-engine`
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid Pro-tier key
- At least one carrier on the active watch list (add via `watchlist_manage` with `action: "add"`)
- Email routing configured at searchcarriers.com/settings/notifications

## Instructions

### Step 1: Retrieve the Active Watch List

Call `manage_watchlist` with `action: "list"`. Process the returned carrier
entries as-is; the documented tool does not promise synthetic monitoring-state
or baseline fields.

```python
watchlist_response = manage_watchlist(action="list")
active_carriers = watchlist_response.get("carriers", [])
if not active_carriers:
    print("No active carriers on watch list. Digest skipped.")
```

### Step 2: Score Risk for Every Active Carrier

For each carrier, call `risk_score` to get a composite score (0-100) and risk level. Classify into two buckets:

| Risk Level | Action |
|------------|--------|
| LOW / MEDIUM | Auto-pass -- skip vetting |
| ELEVATED / HIGH | Proceed to vetting check |

```python
scored = []
for carrier in active_carriers:
    result = risk_score(dot_number=carrier["dot_number"])
    data = result.get("_pipeline", {}).get("data", {})
    scored.append(
        {
            **carrier,
            "composite_score": data.get("composite_score"),
            "risk_level": data.get("risk_level", "UNKNOWN"),
        }
    )

needs_vetting = [c for c in scored if c["risk_level"] in ("ELEVATED", "HIGH")]
auto_passed = [c for c in scored if c["risk_level"] in ("LOW", "MEDIUM")]
```

### Step 3: Vet Elevated and High-Risk Carriers

Call `vetting_check` for each elevated/high carrier. This returns a verdict: PASS, REVIEW, or FAIL.

```python
for carrier in needs_vetting:
    result = vetting_check(dot_number=carrier["dot_number"], ruleset="standard")
    data = result.get("_pipeline", {}).get("data", {})
    carrier["vetting_verdict"] = data.get("verdict", "UNKNOWN")
    carrier["review_items"] = data.get("review_items", [])
    carrier["fail_items"] = data.get("fail_items", [])
```

### Step 4: Generate Detailed Reports for Failures

Any FAIL carrier gets a full vetting report via `generate_report`. REVIEW carriers with 3+ flagged items also get a report (compounded near-threshold risk).

```python
detailed_reports = []
for c in needs_vetting:
    if c["vetting_verdict"] == "FAIL" or (
        c["vetting_verdict"] == "REVIEW" and len(c.get("review_items", [])) >= 3
    ):
        report = generate_report(
            dot_number=c["dot_number"], report_type="vetting_report", format="markdown"
        )
        detailed_reports.append(
            {
                "dot_number": c["dot_number"],
                "legal_name": c["legal_name"],
                "report": report.get("result", {}).get("content", ""),
            }
        )
```

### Step 5: Aggregate and Format the Digest

Classify every carrier into passed/review/failed buckets and compute the fleet health indicator:

| Condition | Indicator | Meaning |
|-----------|-----------|---------|
| 0 failures, 0 reviews | HEALTHY | All carriers qualified |
| 0 failures, 1+ reviews | ATTENTION | Operational but some need review |
| 1-2 failures | AT RISK | Immediate action on failing carriers |
| 3+ failures | CRITICAL | Significant qualification issues |

**Digest Template** (Markdown, email-ready):

```markdown
# Daily Vetting Digest -- 2026-02-26

**Fleet Health: AT RISK**
Carriers monitored: 5 | Passed: 3 | Review: 1 | Failed: 1

---

## Carrier Summary

| DOT | Carrier | Risk Score | Risk Level | Status | Note |
|-----|---------|------------|------------|--------|------|
| 2876421 | HEARTLAND EXPRESS INC | 12/100 | LOW | PASS | Auto-qualified |
| 1018824 | MARTEN TRANSPORT LTD | 22/100 | LOW | PASS | Auto-qualified |
| 3192847 | APEX LOGISTICS LLC | 58/100 | ELEVATED | REVIEW | 2 rule(s) near threshold |
| 1547293 | SUMMIT FREIGHT INC | 41/100 | MEDIUM | PASS | Auto-qualified |
| 2634810 | PINNACLE CARRIERS LLC | 79/100 | HIGH | FAIL | Failed: insurance_active, insurance_minimum |

---

## Carriers Requiring Review (1)

### APEX LOGISTICS LLC -- DOT 3192847
- **Risk Score**: 58/100 (ELEVATED)
- **Review Items**:
  - `authority_age`: Authority 20 months old (threshold: 18mo, within warning margin)
  - `oos_rate`: Vehicle OOS at 24.3% (national avg ~20%, threshold: 30%)
- **Action**: Review OOS trend. If stable, qualify with note. If increasing, request corrective action plan.

---

## Carriers Failing Vetting (1)

### PINNACLE CARRIERS LLC -- DOT 2634810
- **Risk Score**: 79/100 (HIGH)
- **Failed Rules**:
  - `insurance_active`: No active BIPD policy on file
  - `insurance_minimum`: BIPD = $0 (minimum: $750,000)
- **Action**: Suspend freight tenders immediately. Contact carrier for updated COI.

[Full vetting report attached below]
```

### Step 6: Route the Digest via Email

Call `route_alert` with `channel: "email"` to queue the digest for delivery.

```python
route_alert(
    channel="email",
    subject=f"[SearchCarriers] Daily Vetting Digest -- {date} -- {health}",
    body=digest_content,
    alert_type="daily_digest",
    metadata={
        "total": total,
        "passed": len(passed),
        "review": len(review),
        "failed": len(failed),
        "health": health,
    },
)
```

Recipients are resolved from account notification settings. CRITICAL and AT RISK digests go to all configured recipients. HEALTHY digests respect digest frequency preferences (some users suppress all-clear digests).

## Examples

### Example 1: Clean Fleet -- All Carriers Pass

A broker monitoring 12 carriers runs the daily digest. All score LOW/MEDIUM risk. No vetting checks triggered. Digest: "Fleet Health: HEALTHY. 12 passed, 0 review, 0 failed." Total MCP calls: 1 (`manage_watchlist`) + 12 (`risk_score`) + 1 (`route_alert`) = 14.

### Example 2: Mixed Fleet -- Some Need Attention

A 3PL monitors 25 carriers. 20 auto-pass at LOW/MEDIUM. 4 ELEVATED go through vetting: 3 pass, 1 REVIEW for aging MCS-150. 1 HIGH fails due to lapsed BIPD. Digest: "Fleet Health: AT RISK. 23 passed, 1 review, 1 failed." Full report generated for the failure. Total MCP calls: 1 + 25 + 5 + 1 + 1 = 33.

### Example 3: Critical Fleet Emergency

An enterprise account monitors 50 carriers after a major insurer exits the trucking market. 8 show HIGH risk with insurance lapses. Digest: "Fleet Health: CRITICAL. 38 passed, 4 review, 8 failed." Full reports for all 8 failures. Subject: `[SearchCarriers] Daily Vetting Digest -- 2026-02-26 -- CRITICAL`. All contacts notified regardless of frequency preferences.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Empty watch list | No company watches configured | Send an empty digest; suggest adding carriers via `manage_watchlist` |
| `risk_score` fails for one carrier | API timeout or transient error | Mark as UNKNOWN in digest, continue processing remaining carriers |
| `vetting_check` fails | Missing upstream data or tier restriction | Show "VETTING ERROR" status with error message; do not block others |
| `generate_report` fails | Ops Reporter MCP unreachable | Include summary without detailed report; note "report unavailable" |
| `route_alert` fails | Email not configured or delivery error | Display digest directly; suggest configuring at searchcarriers.com/settings |
| Partial watch list | Pagination truncation | Check pagination metadata; issue follow-up calls for remaining pages |
| Rate limiting | Too many calls in rapid succession | Sequential calls with 350ms delays; respect `Retry-After` headers |
| 403 tier restriction | Account below Pro | State: "Daily Vetting Digest requires Pro tier. Upgrade at searchcarriers.com/pricing." |

When any single carrier fails during processing, the workflow continues with remaining carriers. A partial digest is always more useful than no digest.

## Resources

- Ops Reporter skill: `{baseDir}/plugins/searchcarriers-ops-reporter/skills/searchcarriers-ops-reporter/SKILL.md`
- Watchdog skill: `{baseDir}/plugins/searchcarriers-watchdog/skills/searchcarriers-watchdog/SKILL.md`
- Risk Engine skill: `{baseDir}/plugins/searchcarriers-risk-engine/skills/searchcarriers-risk-engine/SKILL.md`
- Pipeline: Carrier Intel (INPUT) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT) + Watchdog (MONITORING)
- Notification settings: searchcarriers.com/settings/notifications
- FMCSA insurance minimums: 49 CFR Part 387
- National OOS benchmarks: vehicle ~20%, driver ~5%
