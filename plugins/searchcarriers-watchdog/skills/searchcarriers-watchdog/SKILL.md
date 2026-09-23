---
name: searchcarriers-watchdog
description: Manage SearchCarriers company watches, format supplied notifications, and run point-in-time compliance checks. Use when operating carrier monitoring.
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
- plugin
---

# SearchCarriers Watchdog

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current
> v3/v2/v1 route map. Do not invent alert or webhook routes.

The Watchdog MCP server manages the SearchCarriers watch configuration and can
evaluate a carrier's current compliance posture. It also formats an alert object
supplied by another system for Slack, Telegram, email, or a generic webhook.

The published SearchCarriers API currently documents watch configuration, not
an alert-feed endpoint. `get_alerts` is retained for client compatibility and
returns `endpoint_unavailable` with the documented alternatives. It does not
claim that an empty response means a carrier is stable.

## Prerequisites

- Pro Plus or higher subscription tier
- `SEARCHCARRIERS_API_KEY` in the MCP server environment
- `searchcarriers-watchdog` MCP server configured and running
- A separate scheduler or notification source when continuous monitoring is
  required

## Instructions

### Manage watches

Use `manage_watchlist` with one of these actions:

| Action | Required input | API behavior |
|---|---|---|
| `list` | None | `GET /api/v1/company/watch` |
| `add` | `dot_number`; optional `watch_types` | `POST /api/v1/company/{dot}/watch` |
| `remove` | `dot_number` | POST the same route with an empty `watch_types` array |

`watch_types` defaults to `["all"]`. The upstream API also documents examples
such as `details` and `inspections`. Preserve the upstream response instead of
inventing baseline dates, alert counts, monitoring states, or retention rules.

### Handle the compatibility alert tool

If a caller invokes `get_alerts`, explain that the public API does not expose an
alert feed. The structured response lists the documented watch routes. Do not
retry the former `/api/v1/carrier-watch/alerts` route and do not interpret the
compatibility response as evidence that no changes occurred.

For automated monitoring, use one of these explicit designs:

1. Consume a notification delivered by the user's configured SearchCarriers
   channel, then pass its alert object to `route_alert` for formatting.
2. Run a scheduled, application-owned comparison of authorized company data,
   persist a minimal baseline outside this plugin, and emit an alert only when
   that comparator detects a change.

### Format a supplied alert

`route_alert` accepts an `alert` object, `channel`, and `destination`. It returns
a channel-ready payload. It does not transmit the payload. The caller owns
delivery, retries, credentials, and audit logging.

Supported formatting channels are `slack`, `telegram`, `email`, and `webhook`.
Before transmitting, validate the destination against an application allowlist
and keep webhook URLs and mail credentials out of logs.

### Run a point-in-time compliance check

Use `monitor_compliance` with a DOT number to evaluate current authority,
insurance, safety rating, and MCS-150 currency. Treat the result as a screening
aid. If upstream sections are unavailable, report the missing evidence rather
than describing the carrier as compliant.

## Examples

### Add a company watch

```json
{
  "action": "add",
  "dot_number": "1234567",
  "watch_types": ["details", "inspections"]
}
```

### Stop watching a company

```json
{"action":"remove","dot_number":"1234567"}
```

### Format an application-owned alert

```json
{
  "alert": {
    "dot_number": "1234567",
    "carrier_name": "EXAMPLE FREIGHT LLC",
    "alertType": "insurance_change",
    "severity": "warning",
    "summary": "Review the current insurance record."
  },
  "channel": "slack",
  "destination": "#carrier-review"
}
```

The returned Slack payload is formatting output. Sending it requires a separate
authorized Slack client or webhook integration.

## Error handling

| Error | Meaning | Action |
|---|---|---|
| `endpoint_unavailable` | No published SearchCarriers alert-feed route | Use a configured notification source or an application-owned comparator |
| `401` | Token rejected | Rotate or correct the API token |
| `403` | Subscription does not cover the operation | Verify the account tier |
| `404` | Company or watch not found | Confirm the DOT number and current watch state |
| `429` | Rate limited | Honor `Retry-After` and use bounded backoff |

## Resources

- Current repository contract: `API-DISCOVERY.md`
- Public API documentation: https://searchcarriers.com/docs/api
- MCP server source: `{baseDir}/scripts/watchdog_mcp.py`
- SearchCarriers terms: https://searchcarriers.com/terms-of-service

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.
