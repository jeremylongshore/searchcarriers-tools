# Carrier Event Slack Formatter

**Validate and format a supplied carrier-change event for Slack delivery.**

`searchcarriers-slack-carrier-watch` | SearchCarriers tier: **proplus** | Version **0.3.0**

## The customer pain

Untrusted event payloads and invented alert feeds create false urgency or expose webhook secrets.

## What this skill changes

Validate and format a supplied carrier-change event for Slack delivery. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Operations teams routing carrier-change events into Slack.
- **When:** “Format this verified authority-change event for our carrier Slack channel.”
- **Evidence:** Watchdog MCP route_alert with externally supplied event; no public SearchCarriers alert-feed route.
- **Customer receives:** Event provenance, carrier, change, current confirmation, severity rationale, owner, and action link.

## Decision contract

Return MESSAGE READY, QUARANTINED, or DELIVERY FAILED.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Missing provenance or DOT is quarantined. endpoint_unavailable is not no alerts.

## Operational follow-through

Send only through a configured Slack integration and preserve the delivery receipt.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
