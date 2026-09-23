---
name: searchcarriers-insurance-lapse-alert
description: Detect insurance cancellations or lapses on watched carriers and send instant alerts via Slack or email. Use when monitoring insurance.
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

# Insurance Lapse Alert -- Workflow Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This workflow orchestrates the Watchdog and Risk Engine plugins into a focused insurance monitoring pipeline. It retrieves the active watch list, runs an insurance check against each watched carrier, detects lapses, cancellations, pending cancellations, and near-expiry policies, then formats critical findings for Slack or email delivery by the caller.

Insurance is a time-sensitive vetting dimension. This workflow produces current evidence and ready-to-send messages; notification timing depends on the caller's schedule and delivery system.

**Cross-plugin orchestration**: This workflow bridges two plugins:
- **searchcarriers-watchdog** -- provides `manage_watchlist` (to retrieve monitored carriers) and `route_alert` (to format notifications)
- **searchcarriers-risk-engine** -- provides `insurance_check` (to validate coverage status per carrier)

**Pipeline position**: Watchdog (MONITORING) + Risk Engine (ANALYSIS) -> Insurance Lapse Alert (WORKFLOW)

## Prerequisites

- **Minimum tier**: Pro Plus
- MCP servers `searchcarriers-watchdog` and `searchcarriers-risk-engine` must both be running and accessible.
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid Pro Plus or Enterprise key.
- At least one carrier must be on the watch list. Use `/sc-watch add {DOT}` to populate the list.
- Notification channel (Slack or email) must be configured at `searchcarriers.com/settings/notifications` for alert routing.
- `python3` must be available in the execution environment.

## Instructions

### Step 1: Retrieve the Active Watch List

Call the `manage_watchlist` MCP tool with `action: "list"` and check each
returned carrier. Do not infer monitoring states, freshness states, alert
counts, or watch dates that the tool did not return.

```python
# Call manage_watchlist with action: "list"
# Returns: list of watched carriers with id, dot_number, and carrier_name

import json
from datetime import datetime


def get_active_watchlist(watchlist_response):
    carriers = watchlist_response.get("carriers", [])
    return carriers, []
```

If the watch list is empty, report: "No carriers on the watch list. Run `/sc-watch add {DOT}` to start monitoring." and stop.

### Step 2: Run Insurance Check for Each Carrier

For each active carrier on the watch list, call the `insurance_check` MCP tool from the Risk Engine plugin. This tool validates BIPD coverage, cargo insurance, bond requirements, pending cancellations, and coverage gaps.

```python
# insurance_check returns per carrier:
#   status: ADEQUATE | WARNING | CRITICAL
#   bipd_active: bool
#   bipd_amount: int (dollar amount)
#   bipd_adequate: bool (meets federal minimum)
#   cargo_active: bool
#   cargo_amount: int
#   bond_required: bool
#   pending_cancellations: list of {policy_type, cancelled_date}
#   coverage_gaps: list of {from_date, to_date, gap_days, severity}


def run_insurance_checks(active_carriers):
    results = []
    for carrier in active_carriers:
        dot = carrier["dot_number"]
        name = carrier["carrier_name"]

        # MCP tool call: insurance_check(dot_number=dot)
        # Returns the _pipeline envelope with insurance data
        check = {
            "dot_number": dot,
            "carrier_name": name,
            "insurance": None,  # populated by MCP response
            "error": None,
        }

        try:
            # result = insurance_check(dot_number=dot)
            # check["insurance"] = result["_pipeline"]["data"]
            pass
        except Exception as e:
            check["error"] = str(e)

        results.append(check)

    return results
```

Process carriers sequentially to respect API rate limits. If a single carrier's check fails, log the error and continue with the remaining carriers. Do not abort the batch.

### Step 3: Detect Lapses, Cancellations, and Near-Expiry

Analyze each insurance check result to identify actionable findings. Classify each finding into one of four categories with corresponding severity.

```python
FINDING_TYPES = {
    "lapse": {
        "severity": "critical",
        "label": "Insurance Lapse",
        "description": "BIPD coverage has lapsed -- carrier cannot legally operate",
    },
    "cancellation": {
        "severity": "critical",
        "label": "Insurance Cancelled",
        "description": "Active BIPD policy cancelled with no replacement on file",
    },
    "pending_cancellation": {
        "severity": "high",
        "label": "Cancellation Pending",
        "description": "BIPD policy will be cancelled on {date} -- request replacement proof",
    },
    "near_expiry": {
        "severity": "high",
        "label": "Coverage Near Expiry",
        "description": "BIPD coverage expires within 30 days with no renewal detected",
    },
    "below_minimum": {
        "severity": "critical",
        "label": "Below Federal Minimum",
        "description": "BIPD coverage amount is below the federal minimum for carrier operation type",
    },
    "cargo_missing": {
        "severity": "medium",
        "label": "Cargo Insurance Missing",
        "description": "No active cargo insurance on file -- not federally required but industry standard",
    },
}


def detect_findings(check_results):
    findings = []

    for result in check_results:
        if result["error"]:
            findings.append(
                {
                    "dot_number": result["dot_number"],
                    "carrier_name": result["carrier_name"],
                    "type": "check_error",
                    "severity": "high",
                    "detail": f"Insurance check failed: {result['error']}",
                }
            )
            continue

        ins = result["insurance"]
        dot = result["dot_number"]
        name = result["carrier_name"]

        # CRITICAL: BIPD not active
        if not ins.get("bipd_active"):
            findings.append(
                {
                    "dot_number": dot,
                    "carrier_name": name,
                    "type": "lapse",
                    "severity": "critical",
                    "detail": FINDING_TYPES["lapse"]["description"],
                }
            )

        # CRITICAL: BIPD below federal minimum
        elif not ins.get("bipd_adequate"):
            amount = ins.get("bipd_amount", 0)
            findings.append(
                {
                    "dot_number": dot,
                    "carrier_name": name,
                    "type": "below_minimum",
                    "severity": "critical",
                    "detail": f"BIPD coverage ${amount:,} is below federal minimum",
                }
            )

        # HIGH: Pending cancellations
        for pc in ins.get("pending_cancellations", []):
            cancel_date = pc.get("cancelled_date", "unknown")
            findings.append(
                {
                    "dot_number": dot,
                    "carrier_name": name,
                    "type": "pending_cancellation",
                    "severity": "high",
                    "detail": f"{pc.get('policy_type', 'BIPD')} cancellation pending on {cancel_date}",
                }
            )

        # CRITICAL: Historical coverage gaps (recent, within 90 days)
        for gap in ins.get("coverage_gaps", []):
            if gap.get("severity") == "SEVERE":
                findings.append(
                    {
                        "dot_number": dot,
                        "carrier_name": name,
                        "type": "cancellation",
                        "severity": "critical",
                        "detail": f"Coverage gap: {gap['from_date']} to {gap['to_date']} ({gap['gap_days']} days)",
                    }
                )

        # MEDIUM: No cargo insurance
        if not ins.get("cargo_active"):
            findings.append(
                {
                    "dot_number": dot,
                    "carrier_name": name,
                    "type": "cargo_missing",
                    "severity": "medium",
                    "detail": FINDING_TYPES["cargo_missing"]["description"],
                }
            )

    return findings
```

### Step 4: Route Critical Findings as Alerts

For each finding classified as critical or high severity, call the `route_alert` MCP tool from the Watchdog plugin to send an instant notification. Medium-severity findings are included in the summary but not routed as instant alerts unless the user explicitly requests it.

```python
SEVERITY_ROUTING = {
    "critical": {
        "channels": ["slack", "email"],  # Critical goes to both
        "slack_color": "#E01E5A",
        "slack_mention": "<!channel>",
        "email_priority": "immediate",
    },
    "high": {
        "channels": ["slack"],  # High goes to Slack only
        "slack_color": "#ECB22E",
        "slack_mention": "<!here>",
        "email_priority": "hourly_digest",
    },
    "medium": {
        "channels": [],  # Medium: summary only, no instant routing
        "slack_color": "#36C5F0",
        "slack_mention": "",
        "email_priority": "daily_digest",
    },
}


def route_findings(findings, target_channel="slack"):
    routed = {"delivered": [], "skipped": [], "failed": []}

    for finding in findings:
        severity = finding["severity"]
        routing = SEVERITY_ROUTING[severity]

        # Only route critical and high findings instantly
        if target_channel not in routing["channels"]:
            routed["skipped"].append(finding)
            continue

        # MCP tool call: route_alert
        route_params = {
            "alert_id": f"ins_{finding['dot_number']}_{finding['type']}",
            "channel": target_channel,
            "payload": {
                "carrier_name": finding["carrier_name"],
                "dot_number": finding["dot_number"],
                "alert_type": finding["type"],
                "severity": severity,
                "description": finding["detail"],
            },
        }

        try:
            # MCP call: route_alert(route_params)
            routed["delivered"].append(finding)
        except Exception as e:
            finding["error"] = str(e)
            routed["failed"].append(finding)

    return routed
```

### Step 5: Generate the Insurance Monitoring Summary

Produce a consolidated summary of all findings and routing results.

```
INSURANCE LAPSE ALERT -- MONITORING SUMMARY
Run at:       {timestamp}
Carriers:     {active_count} watched, {failed_count} check failures
Channel:      {target_channel}

FINDINGS
| # | Severity | DOT     | Carrier              | Type                  | Detail                    |
|---|----------|---------|----------------------|-----------------------|---------------------------|
| 1 | CRITICAL | 1234567 | ACME TRUCKING LLC    | Insurance Lapse       | BIPD coverage lapsed      |
| 2 | HIGH     | 2345678 | FAST FREIGHT INC     | Cancellation Pending  | BIPD cancelled 2026-03-15 |
| 3 | MEDIUM   | 3456789 | ROAD RUNNER TRANSPORT| Cargo Missing         | No cargo insurance filed  |

ROUTING STATUS
  Critical messages formatted: {count}
  High messages formatted:     {count}
  Medium findings:             {count} (summary only)
  Formatting failures:         {count}

{if failed_count > 0}
CHECK FAILURES
| DOT     | Carrier              | Error |
|---------|----------------------|-------|
| {dot}   | {name}               | {error} |
Retry after verifying authentication, plan access, and API availability.
{end if}

{if no findings}
ALL CLEAR
No insurance issues detected across {active_count} watched carriers.
All BIPD policies are active and meet federal minimums.
{end if}

NEXT STEPS
- For CRITICAL findings: suspend freight tenders and contact carrier immediately
- Run `/sc-risk {DOT}` for full risk reassessment on flagged carriers
- Run `/sc-vet {DOT}` to re-evaluate qualification after insurance is resolved
- Run `/sc-watch` to manage the carrier watch list
```

## Examples

### Example 1: Routine Insurance Scan

**User prompt**: "Check insurance on all watched carriers"

1. Call `manage_watchlist` with `action: "list"` -- returns 12 active carriers, 1 stale.
2. Run `insurance_check` for each of the 12 active carriers.
3. Detect findings: 1 carrier with pending cancellation (high), 2 with missing cargo (medium).
4. Route the pending cancellation alert to Slack.
5. Display summary: "12 carriers checked. 1 high alert (pending cancellation) routed to Slack. 2 medium findings (cargo missing) in summary only. 1 stale carrier skipped."

### Example 2: Critical Lapse Detected

**User prompt**: "Run insurance lapse check and alert me"

1. Retrieve 8 active carriers from watch list.
2. Insurance check reveals DOT 1234567 has no active BIPD -- lapse detected.
3. Classify as CRITICAL finding.
4. Route to both Slack (red card, @channel) and email (immediate delivery).
5. Display: "CRITICAL: Insurance lapse detected for DOT 1234567 (ACME TRUCKING LLC). BIPD coverage has lapsed. Alert sent to Slack and email. Suspend freight tenders immediately."

### Example 3: All Clear

**User prompt**: "Any insurance issues on my watched carriers?"

1. Retrieve 5 active carriers from watch list.
2. Run insurance check on all 5 -- all return status ADEQUATE.
3. No findings generated.
4. Display: "All clear. All 5 watched carriers have active BIPD coverage meeting federal minimums. No pending cancellations detected."

### Example 4: Email-Only Routing

**User prompt**: "Check insurance and send alerts via email"

1. Retrieve active watch list and run insurance checks.
2. Detect 2 findings (1 critical lapse, 1 high pending cancellation).
3. Route both via `route_alert` with `channel: "email"`.
4. Critical alert sent with immediate priority; high alert queued for hourly digest.
5. Display summary with email delivery confirmation.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|---|---|---|
| MCP tool `manage_watchlist` not available | Watchdog server not running | Check `.mcp.json` and restart `searchcarriers-watchdog` MCP server |
| MCP tool `insurance_check` not available | Risk Engine server not running | Check `.mcp.json` and restart `searchcarriers-risk-engine` MCP server |
| MCP tool `route_alert` not available | Watchdog server not running | Check `.mcp.json` and restart `searchcarriers-watchdog` MCP server |
| 401 Unauthorized | Invalid or expired API key | Verify `SEARCHCARRIERS_API_KEY` is set with a Pro Plus key |
| 403 Tier Restriction | Account tier below Pro Plus | State: "Insurance Lapse Alert requires Pro Plus. Upgrade at searchcarriers.com/pricing." |
| Empty watch list | No carriers being monitored | State: "No carriers on watch list. Run `/sc-watch add {DOT}` to start monitoring." |
| Insurance check fails for one carrier | API error or invalid DOT | Log the error, skip the carrier, continue with remaining; report failures in summary |
| All insurance checks fail | API outage or authentication issue | Abort workflow; state: "Insurance checks failed for all carriers. Verify API key and connectivity." |
| Route channel not configured | Slack or email integration missing | Direct user to searchcarriers.com/settings/notifications |
| Slack delivery failure | Webhook URL invalid or Slack API down | Retry once; on failure, fall back to email if configured; display alerts in console as last resort |
| Rate limit (429) on insurance_check | Too many API calls | Add 1-second delay between checks; for large watch lists (50+), batch in groups of 10 |
| Stale carrier data | Carrier removed from FMCSA database | Flag as stale in watch list; suggest removal via `/sc-watch remove {DOT}` |

## Resources

- Watchdog plugin schema: `{baseDir}/plugins/searchcarriers-watchdog/SCHEMA.md`
- Watchdog skill: `{baseDir}/plugins/searchcarriers-watchdog/skills/searchcarriers-watchdog/SKILL.md`
- Risk Engine plugin schema: `{baseDir}/plugins/searchcarriers-risk-engine/SCHEMA.md`
- Risk Engine skill: `{baseDir}/plugins/searchcarriers-risk-engine/skills/searchcarriers-risk-engine/SKILL.md`
- Insurance Validator skill: `{baseDir}/skills/vetting-risk/searchcarriers-insurance-validator/SKILL.md`
- FMCSA insurance requirements: 49 CFR Part 387
- Federal BIPD minimums: General freight $750K, hazmat (bulk) $5M, passengers $1.5-5M
- Pipeline architecture: Carrier Intel (INPUT) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT) + Watchdog (MONITORING)
- Notification settings: searchcarriers.com/settings/notifications
