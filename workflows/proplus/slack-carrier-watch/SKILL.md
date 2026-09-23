---
name: searchcarriers-slack-carrier-watch
description: Format externally supplied carrier notifications for Slack. Use when an application already has a SearchCarriers notification or detected change.
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

# Slack carrier notification formatting

## Overview

> **API contract:** The published SearchCarriers API does not expose an alert
> feed. This workflow starts with an alert supplied by an external notification
> channel or an application-owned comparator.

Use the Watchdog `route_alert` tool to turn a supplied carrier-change object
into a Slack Block Kit payload. The tool formats only; an authorized Slack
client performs delivery.

## Prerequisites

- Watchdog MCP server and Pro Plus or higher tier
- A validated alert object from a configured SearchCarriers notification or an
  application-owned comparison job
- A separately authorized Slack delivery mechanism

## Instructions

1. Validate that the alert identifies a DOT number, change type, timestamp, and
   source. Reject free-form objects whose origin cannot be established.
2. Classify urgency using the organization's approved carrier policy. Avoid
   converting missing data into a “safe” status.
3. Call `route_alert` with the full alert, `channel: "slack"`, and the logical
   destination.
4. Inspect the returned payload. Do not describe it as delivered yet.
5. Send it through the separately configured Slack integration, record the
   delivery result, and retry only with bounded backoff and deduplication.

## Examples

```json
{
  "alert": {
    "dot_number": "1234567",
    "carrier_name": "EXAMPLE FREIGHT LLC",
    "alertType": "authority_change",
    "severity": "warning",
    "summary": "Authority data changed; re-run the current vetting check.",
    "timestamp": "2026-09-22T18:00:00Z"
  },
  "channel": "slack",
  "destination": "#carrier-review"
}
```

After formatting, report separate statuses for `formatted` and `delivered`.

## Error handling

- If `get_alerts` returns `endpoint_unavailable`, stop and request an external
  alert input. Do not treat it as “no alerts.”
- If Slack delivery fails, retain the source event ID for deduplication and
  report the failure without exposing the webhook URL.
- If the alert lacks provenance or a DOT number, quarantine it for review.

## Resources

- Current repository contract: `API-DISCOVERY.md`
- Watchdog skill: `searchcarriers-watchdog`
- Slack Block Kit: https://api.slack.com/block-kit

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.
